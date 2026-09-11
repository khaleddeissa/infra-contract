"""
MCP server
==========

This module is deliberately thin. It calls the exact same
`engine.evaluator.Evaluator`, the exact same providers, and
the exact same `Contract` loader used by the CLI and the GitHub Action.

    AI agent  --(MCP)-->  this file  --(function call)-->  engine

If a check can be answered here, it can be answered identically by running
`infra-contract check` by hand — that parity is the whole point: an agent
proposing infrastructure gets exactly what CI will enforce, before it opens
a PR.
"""

from __future__ import annotations

import json

from cli.common import build_document, load_contract_or_exit
from contracts.models import Contract
from engine.evaluator import Evaluator
from engine.risk import classify_all, requires_human_approval
from mcp.server.fastmcp import FastMCP
from providers.terraform.provider import TerraformProvider

mcp_app = FastMCP("infra-contract")

_DEFAULT_CONTRACT_PATH: str | None = None


def _contract() -> Contract:
    return load_contract_or_exit(_DEFAULT_CONTRACT_PATH)


@mcp_app.tool()
def infra_contract_get_contract() -> str:
    """Return the full infrastructure contract for this project as JSON.

    Use this before generating any infrastructure so you know what is
    allowed, forbidden, and required.
    """
    contract = _contract()
    return json.dumps(contract.model_dump(mode="json", by_alias=True), indent=2)


@mcp_app.tool()
def infra_contract_get_architecture() -> str:
    """Return the approved architecture: allowed compute, database, cache,
    storage components, and allowed cloud regions.
    """
    contract = _contract()
    return json.dumps(
        {
            "cloud_provider": contract.cloud.provider,
            "allowed_regions": contract.cloud.allowed_regions,
            "compute_allowed": contract.architecture.compute.allowed,
            "database_allowed": contract.architecture.database.allowed,
            "cache_allowed": contract.architecture.cache.allowed,
            "storage_allowed": contract.architecture.storage.allowed,
        },
        indent=2,
    )


@mcp_app.tool()
def infra_contract_get_policy(policy_id: str | None = None) -> str:
    """Return one policy's rule (by id, e.g. 'security.no-public-database'),
    or every enabled policy id if no id is given.
    """
    from policies.builtin import ALL_BUILTIN_POLICIES, POLICY_BY_ID

    contract = _contract()
    if policy_id:
        policy = POLICY_BY_ID.get(policy_id)
        if policy is None:
            return json.dumps({"error": f"Unknown policy id: {policy_id}"})
        return json.dumps(
            {
                "id": policy.id,
                "category": policy.category,
                "severity": policy.default_severity.value,
                "enabled": contract.is_policy_enabled(policy.id),
            }
        )
    return json.dumps([p.id for p in ALL_BUILTIN_POLICIES if contract.is_policy_enabled(p.id)])


@mcp_app.tool()
def infra_contract_check(target: str = ".") -> str:
    """Validate a directory of Terraform source against the contract and
    return violations as JSON. Lower confidence than `infra_contract_plan`
    since no plan has been generated yet — good for a quick pre-flight check
    while iterating on generated Terraform.
    """
    contract = _contract()
    document = build_document(target=target)
    evaluator = Evaluator()
    result = evaluator.run(document, contract)
    return json.dumps(result.to_dict(), indent=2)


@mcp_app.tool()
def infra_contract_check_plan(plan_json_path: str) -> str:
    """Validate a `terraform show -json` plan file against the contract.
    This is the high-confidence check: run this on the actual proposed
    infrastructure changes before presenting them as final.
    """
    contract = _contract()
    document = build_document(plan_path=plan_json_path)
    evaluator = Evaluator()
    result = evaluator.run(document, contract)
    return json.dumps(result.to_dict(), indent=2)


@mcp_app.tool()
def infra_contract_explain_violation(rule_id: str, target: str = ".") -> str:
    """Explain why a specific rule id (e.g. 'security.no-public-database')
    is currently failing, including the resource and recommended fix.
    """
    contract = _contract()
    document = build_document(target=target)
    evaluator = Evaluator()
    result = evaluator.run(document, contract)
    matches = [f for f in result.failed_findings if f.rule == rule_id]
    if not matches:
        return json.dumps({"result": f"No current violations for rule '{rule_id}'."})
    return json.dumps([f.to_dict() for f in matches], indent=2)


@mcp_app.tool()
def infra_contract_get_change_risk(plan_json_path: str) -> str:
    """Classify the risk (low/medium/high/critical) of every change in a
    Terraform plan, and report whether human approval is required before
    it can be deployed.
    """
    contract = _contract()
    document = build_document(plan_path=plan_json_path)
    risks = classify_all(document.resources, contract)
    blocked = requires_human_approval(risks, contract)
    return json.dumps(
        {"risks": [r.to_dict() for r in risks], "requires_human_approval": blocked}, indent=2
    )


@mcp_app.tool()
def infra_contract_validate_change(resource_type: str, attributes_json: str) -> str:
    """Ask, before writing any Terraform, whether a single proposed resource
    would pass the contract. `attributes_json` should be a JSON object of
    the resource's planned Terraform attributes (e.g. for aws_db_instance:
    {"publicly_accessible": true, "engine": "postgres"}).

    This lets an agent check an idea ("can I make this bucket public?")
    without generating a full plan first.
    """
    contract = _contract()
    provider = TerraformProvider()
    attrs = json.loads(attributes_json)

    fake_plan = {
        "resource_changes": [
            {
                "address": f"{resource_type}.proposed",
                "type": resource_type,
                "change": {"actions": ["create"], "after": attrs},
            }
        ]
    }
    document = provider.normalize(fake_plan)
    if not document.resources:
        return json.dumps(
            {"result": f"'{resource_type}' is not a modeled resource type; no opinion available."}
        )

    evaluator = Evaluator()
    result = evaluator.run(document, contract)
    if result.failed_findings:
        return json.dumps(
            {"decision": "DENIED", "violations": [f.to_dict() for f in result.failed_findings]},
            indent=2,
        )
    return json.dumps({"decision": "ALLOWED"})


def serve(contract_path: str | None = None) -> None:
    global _DEFAULT_CONTRACT_PATH
    _DEFAULT_CONTRACT_PATH = contract_path
    mcp_app.run()
