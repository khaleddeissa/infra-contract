from __future__ import annotations

from contracts.models import Contract, Severity
from engine.findings import Finding
from ir.model import Resource, ResourceKind
from policies.base import Policy


class ProductionDatabasePrivatePolicy(Policy):
    id = "networking.production-database-private"
    category = "networking"
    default_severity = Severity.CRITICAL

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.DATABASE and resource.is_production()

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        must_be_private = contract.networking.database.private_subnet_required
        violated = must_be_private and resource.network.public
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                "Production database is reachable from a public subnet."
                if violated
                else "Production database is in a private network boundary."
            ),
            expected="private_subnet_required = true",
            actual=f"public = {resource.network.public}",
            remediation=(
                "Move the database to a private subnet with no public route." if violated else None
            ),
        )


class RestrictedIngressPolicy(Policy):
    id = "networking.restricted-ingress"
    category = "networking"
    default_severity = Severity.HIGH

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.NETWORK

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        open_to_world = "0.0.0.0/0" in resource.network.ingress_cidrs
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not open_to_world,
            message=(
                "Security group allows ingress from 0.0.0.0/0."
                if open_to_world
                else "Security group ingress is restricted."
            ),
            expected="no ingress rule with cidr 0.0.0.0/0",
            actual=f"ingress_cidrs = {resource.network.ingress_cidrs}",
            remediation=(
                "Restrict ingress to known CIDR ranges or a load balancer security group."
                if open_to_world
                else None
            ),
        )


BUILTIN_NETWORKING_POLICIES: list[Policy] = [
    ProductionDatabasePrivatePolicy(),
    RestrictedIngressPolicy(),
]
