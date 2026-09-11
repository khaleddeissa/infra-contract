from __future__ import annotations

from contracts.models import Contract, Severity
from engine.findings import Finding
from ir.model import Resource, ResourceKind
from policies.base import Policy


class ProductionBackupsRequiredPolicy(Policy):
    id = "reliability.production-backups"
    category = "reliability"
    default_severity = Severity.HIGH

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.DATABASE and resource.is_production()

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        required = contract.reliability.production.backups == "required"
        enabled = resource.reliability.backups_enabled
        violated = required and enabled is False
        unknown = required and enabled is None
        return Finding(
            rule=self.id,
            severity=self.default_severity if violated else Severity.WARNING,
            resource_id=resource.id,
            category=self.category,
            passed=not violated and not unknown,
            message=(
                "Automated backups are disabled for a production database."
                if violated
                else (
                    "Could not confirm backup configuration."
                    if unknown
                    else "Automated backups are enabled."
                )
            ),
            expected="backups = required",
            actual=f"backups_enabled = {enabled}",
            remediation="Set backup_retention_period > 0." if violated else None,
        )


class ProductionMultiAzPolicy(Policy):
    id = "reliability.production-multi-az"
    category = "reliability"
    default_severity = Severity.MEDIUM

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.DATABASE and resource.is_production()

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        required = contract.reliability.production.multi_az == "required"
        enabled = resource.reliability.multi_az
        violated = required and enabled is False
        unknown = required and enabled is None
        return Finding(
            rule=self.id,
            severity=self.default_severity if violated else Severity.WARNING,
            resource_id=resource.id,
            category=self.category,
            passed=not violated and not unknown,
            message=(
                "Production database is not Multi-AZ."
                if violated
                else (
                    "Could not confirm Multi-AZ configuration."
                    if unknown
                    else "Production database is Multi-AZ."
                )
            ),
            expected="multi_az = required",
            actual=f"multi_az = {enabled}",
            remediation="Set multi_az = true." if violated else None,
        )


BUILTIN_RELIABILITY_POLICIES: list[Policy] = [
    ProductionBackupsRequiredPolicy(),
    ProductionMultiAzPolicy(),
]
