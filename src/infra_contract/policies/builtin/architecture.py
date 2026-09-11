from __future__ import annotations

from infra_contract.contracts.models import Contract, Severity
from infra_contract.engine.findings import Finding
from infra_contract.ir.model import Resource, ResourceKind
from infra_contract.policies.base import Policy

_KIND_TO_TERRAFORM_COMPONENT = {
    # maps normalized resource_type -> the short name used in
    # architecture.compute.allowed / architecture.database.allowed, etc.
    "aws_ecs_service": "ecs",
    "aws_lambda_function": "lambda",
    "aws_instance": "ec2",
    "aws_db_instance": "rds-postgres",
    "aws_rds_cluster": "rds-postgres",
    "aws_elasticache_replication_group": "elasticache-redis",
    "aws_elasticache_cluster": "elasticache-redis",
}


class ApprovedComputeOnlyPolicy(Policy):
    id = "architecture.approved-compute-only"
    category = "architecture"
    default_severity = Severity.HIGH

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.COMPUTE

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        allowed = contract.architecture.compute.allowed
        component = _KIND_TO_TERRAFORM_COMPONENT.get(resource.resource_type, resource.resource_type)
        violated = bool(allowed) and component not in allowed
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                f"Compute type '{component}' is not an approved compute component."
                if violated
                else f"Compute type '{component}' is approved."
            ),
            expected=f"compute.allowed = {allowed}",
            actual=f"compute = {component}",
            remediation=f"Use one of the approved compute types: {allowed}." if violated else None,
        )


class ApprovedDatabaseOnlyPolicy(Policy):
    id = "architecture.approved-database-only"
    category = "architecture"
    default_severity = Severity.HIGH

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.DATABASE

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        allowed = contract.architecture.database.allowed
        component = _KIND_TO_TERRAFORM_COMPONENT.get(resource.resource_type, resource.resource_type)
        violated = bool(allowed) and component not in allowed
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                f"Database type '{component}' is not an approved database component."
                if violated
                else f"Database type '{component}' is approved."
            ),
            expected=f"database.allowed = {allowed}",
            actual=f"database = {component}",
            remediation=f"Use one of the approved database types: {allowed}." if violated else None,
        )


class ApprovedRegionOnlyPolicy(Policy):
    id = "architecture.approved-region-only"
    category = "architecture"
    default_severity = Severity.MEDIUM

    def applies_to(self, resource: Resource) -> bool:
        return resource.region is not None

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        allowed = contract.cloud.allowed_regions
        violated = bool(allowed) and resource.region not in allowed
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                f"Resource is deployed in disallowed region '{resource.region}'."
                if violated
                else f"Resource region '{resource.region}' is approved."
            ),
            expected=f"regions.allowed = {allowed}",
            actual=f"region = {resource.region}",
            remediation=f"Move the resource to one of: {allowed}." if violated else None,
        )


BUILTIN_ARCHITECTURE_POLICIES: list[Policy] = [
    ApprovedComputeOnlyPolicy(),
    ApprovedDatabaseOnlyPolicy(),
    ApprovedRegionOnlyPolicy(),
]
