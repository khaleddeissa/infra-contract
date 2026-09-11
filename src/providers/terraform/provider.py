"""
Terraform / OpenTofu provider
=============================

This is the *only* module in the codebase that understands Terraform's JSON
plan format. Everything downstream (policies, engine, CLI, MCP) only ever
sees `ir.model.InfrastructureDocument`.

Preferred integration (higher confidence than parsing raw .tf source):

    terraform plan -out=tfplan
    terraform show -json tfplan > tfplan.json
    infra-contract check --plan tfplan.json

A lower-confidence "source scan" mode is also supported for a quick check
before a plan exists (`from_source_dir`), based on naive attribute matching
in `.tf` files. It is intentionally conservative: on doubt, it emits no
opinion rather than a false pass/fail.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ir.model import (
    ChangeAction,
    InfrastructureDocument,
    NetworkProperties,
    ReliabilityProperties,
    Resource,
    ResourceKind,
    SecurityProperties,
)
from providers.base import InfrastructureProvider

_ACTION_MAP = {
    ("create",): ChangeAction.CREATE,
    ("update",): ChangeAction.UPDATE,
    ("delete",): ChangeAction.DELETE,
    ("no-op",): ChangeAction.NO_OP,
    ("delete", "create"): ChangeAction.REPLACE,
    ("create", "delete"): ChangeAction.REPLACE,
    ("read",): ChangeAction.NO_OP,
}


def _map_action(actions: list[str]) -> ChangeAction:
    return _ACTION_MAP.get(tuple(actions), ChangeAction.UPDATE)


def _extract_db_instance(address: str, attrs: dict[str, Any]) -> Resource:
    return Resource(
        id=address,
        kind=ResourceKind.DATABASE,
        provider="aws",
        resource_type="aws_db_instance",
        engine=attrs.get("engine"),
        region=attrs.get("region"),
        environment=_infer_environment(address, attrs),
        network=NetworkProperties(public=bool(attrs.get("publicly_accessible", False))),
        security=SecurityProperties(encrypted=attrs.get("storage_encrypted")),
        reliability=ReliabilityProperties(
            backups_enabled=(
                (attrs.get("backup_retention_period") or 0) > 0
                if attrs.get("backup_retention_period") is not None
                else None
            ),
            multi_az=attrs.get("multi_az"),
            deletion_protection=attrs.get("deletion_protection"),
        ),
    )


def _extract_s3_bucket(address: str, attrs: dict[str, Any]) -> Resource:
    acl = attrs.get("acl")
    is_public = acl in ("public-read", "public-read-write")
    return Resource(
        id=address,
        kind=ResourceKind.STORAGE,
        provider="aws",
        resource_type="aws_s3_bucket",
        region=attrs.get("region"),
        environment=_infer_environment(address, attrs),
        network=NetworkProperties(public=is_public),
        security=SecurityProperties(
            encrypted=_has_sse(attrs),
        ),
    )


def _has_sse(attrs: dict[str, Any]) -> bool | None:
    rule = attrs.get("server_side_encryption_configuration")
    if rule is None:
        return None
    return bool(rule)


def _extract_security_group(address: str, attrs: dict[str, Any]) -> Resource:
    ingress = attrs.get("ingress") or []
    cidrs: list[str] = []
    for rule in ingress:
        cidrs.extend(rule.get("cidr_blocks") or [])
    return Resource(
        id=address,
        kind=ResourceKind.NETWORK,
        provider="aws",
        resource_type="aws_security_group",
        environment=_infer_environment(address, attrs),
        network=NetworkProperties(
            public="0.0.0.0/0" in cidrs,
            ingress_cidrs=cidrs,
        ),
    )


def _extract_iam_policy(address: str, attrs: dict[str, Any]) -> Resource:
    policy_doc = attrs.get("policy")
    wildcard = False
    if isinstance(policy_doc, str):
        try:
            parsed = json.loads(policy_doc)
            statements = parsed.get("Statement", [])
            if isinstance(statements, dict):
                statements = [statements]
            for stmt in statements:
                action = stmt.get("Action")
                resource = stmt.get("Resource")
                actions = action if isinstance(action, list) else [action]
                resources = resource if isinstance(resource, list) else [resource]
                if "*" in actions or "*" in resources:
                    wildcard = True
        except (json.JSONDecodeError, AttributeError):
            wildcard = "*" in policy_doc
    return Resource(
        id=address,
        kind=ResourceKind.IAM,
        provider="aws",
        resource_type="aws_iam_policy",
        environment=_infer_environment(address, attrs),
        security=SecurityProperties(wildcard_permissions=wildcard),
    )


def _extract_ecs_service(address: str, attrs: dict[str, Any]) -> Resource:
    return Resource(
        id=address,
        kind=ResourceKind.COMPUTE,
        provider="aws",
        resource_type="aws_ecs_service",
        region=attrs.get("region"),
        environment=_infer_environment(address, attrs),
    )


def _extract_lambda(address: str, attrs: dict[str, Any]) -> Resource:
    return Resource(
        id=address,
        kind=ResourceKind.COMPUTE,
        provider="aws",
        resource_type="aws_lambda_function",
        region=attrs.get("region"),
        environment=_infer_environment(address, attrs),
    )


def _extract_ec2_instance(address: str, attrs: dict[str, Any]) -> Resource:
    return Resource(
        id=address,
        kind=ResourceKind.COMPUTE,
        provider="aws",
        resource_type="aws_instance",
        region=attrs.get("region"),
        environment=_infer_environment(address, attrs),
        network=NetworkProperties(public=bool(attrs.get("associate_public_ip_address", False))),
    )


def _extract_elasticache(address: str, attrs: dict[str, Any]) -> Resource:
    return Resource(
        id=address,
        kind=ResourceKind.CACHE,
        provider="aws",
        resource_type="aws_elasticache_replication_group",
        engine=attrs.get("engine", "redis"),
        environment=_infer_environment(address, attrs),
        security=SecurityProperties(encrypted=attrs.get("at_rest_encryption_enabled")),
    )


def _infer_environment(address: str, attrs: dict[str, Any]) -> str | None:
    tags = attrs.get("tags") or {}
    for key in ("Environment", "environment", "env"):
        if key in tags:
            return str(tags[key]).lower()
    lowered = address.lower()
    for candidate in ("production", "prod", "staging", "dev"):
        if candidate in lowered:
            return "production" if candidate in ("production", "prod") else candidate
    return None


# Registry: terraform resource type -> extractor function
_EXTRACTORS: dict[str, Callable[[str, dict[str, Any]], Resource]] = {
    "aws_db_instance": _extract_db_instance,
    "aws_rds_cluster": _extract_db_instance,
    "aws_s3_bucket": _extract_s3_bucket,
    "aws_security_group": _extract_security_group,
    "aws_iam_policy": _extract_iam_policy,
    "aws_iam_role_policy": _extract_iam_policy,
    "aws_ecs_service": _extract_ecs_service,
    "aws_lambda_function": _extract_lambda,
    "aws_instance": _extract_ec2_instance,
    "aws_elasticache_replication_group": _extract_elasticache,
    "aws_elasticache_cluster": _extract_elasticache,
}


class TerraformProvider(InfrastructureProvider):
    name = "terraform"

    def discover(self, path: Path) -> bool:
        if path.is_file():
            return path.suffix == ".tf" or path.name.endswith(".tfplan.json")
        return any(path.glob("*.tf")) or any(path.glob("**/*.tf"))

    # -- Plan-based parsing (preferred, higher confidence) ------------------

    def parse(self, path: Path) -> dict:
        """Parse a `terraform show -json` plan file."""
        return json.loads(Path(path).read_text())

    def normalize(self, parsed: dict) -> InfrastructureDocument:
        resources: list[Resource] = []
        for change in parsed.get("resource_changes", []):
            resource_type = change.get("type", "")
            address = change.get("address", resource_type)
            actions = change.get("change", {}).get("actions", ["no-op"])
            after = change.get("change", {}).get("after") or {}
            before = change.get("change", {}).get("before") or {}
            attrs = after or before

            extractor = _EXTRACTORS.get(resource_type)
            if extractor is None:
                continue  # unmodeled resource type: no opinion, not a false pass

            resource = extractor(address, attrs)
            resource.action = _map_action(actions)
            resource.raw = change
            resources.append(resource)

        return InfrastructureDocument(source="terraform-plan", resources=resources)

    # -- Source-based parsing (fallback, lower confidence) -------------------

    def from_source_dir(self, path: Path) -> InfrastructureDocument:
        """Best-effort scan of raw .tf files without a plan.

        This uses naive regex matching per resource block and is meant only
        as a fast pre-plan sanity check, per the project design principle
        that plan validation is higher confidence than source validation.
        """
        resources: list[Resource] = []
        block_re = re.compile(
            r'resource\s+"(?P<type>\w+)"\s+"(?P<name>\w+)"\s*\{(?P<body>.*?)\n\}',
            re.DOTALL,
        )
        for tf_file in path.glob("**/*.tf"):
            text = tf_file.read_text()
            for match in block_re.finditer(text):
                resource_type = match.group("type")
                name = match.group("name")
                body = match.group("body")
                extractor = _EXTRACTORS.get(resource_type)
                if extractor is None:
                    continue
                attrs = _naive_attrs_from_hcl(body)
                address = f"{resource_type}.{name}"
                resource = extractor(address, attrs)
                resource.raw = {"source_file": str(tf_file)}
                resources.append(resource)
        return InfrastructureDocument(source="terraform-source", resources=resources)


_BOOL_ATTR_RE = re.compile(r"(\w+)\s*=\s*(true|false)", re.IGNORECASE)
_STR_ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
_NUM_ATTR_RE = re.compile(r"(\w+)\s*=\s*(\d+)")


def _naive_attrs_from_hcl(body: str) -> dict[str, Any]:
    attrs: dict[str, Any] = {}
    for key, val in _BOOL_ATTR_RE.findall(body):
        attrs[key] = val.lower() == "true"
    for key, val in _STR_ATTR_RE.findall(body):
        attrs.setdefault(key, val)
    for key, val in _NUM_ATTR_RE.findall(body):
        attrs.setdefault(key, int(val))
    return attrs
