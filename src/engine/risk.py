from __future__ import annotations

from enum import Enum

from contracts.models import Contract
from ir.model import ChangeAction, Resource, ResourceKind


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeRisk:
    def __init__(self, resource_id: str, level: RiskLevel, reason: str):
        self.resource_id = resource_id
        self.level = level
        self.reason = reason

    def to_dict(self) -> dict:
        return {"resource_id": self.resource_id, "level": self.level.value, "reason": self.reason}


def classify_change(resource: Resource, contract: Contract) -> ChangeRisk:
    """A conservative, explainable risk heuristic for a single planned change."""
    is_stateful = resource.kind in (ResourceKind.DATABASE, ResourceKind.STORAGE, ResourceKind.CACHE)

    if resource.action in (ChangeAction.DELETE, ChangeAction.REPLACE) and is_stateful:
        return ChangeRisk(
            resource.id,
            RiskLevel.CRITICAL,
            "Stateful resource will be destroyed or replaced.",
        )

    if resource.kind == ResourceKind.NETWORK and resource.action != ChangeAction.NO_OP:
        return ChangeRisk(
            resource.id, RiskLevel.HIGH, "Security group / ingress rules are changing."
        )

    if resource.kind == ResourceKind.IAM and resource.action != ChangeAction.NO_OP:
        return ChangeRisk(resource.id, RiskLevel.HIGH, "IAM permissions are changing.")

    if is_stateful and resource.action == ChangeAction.UPDATE:
        return ChangeRisk(
            resource.id, RiskLevel.MEDIUM, "Stateful resource configuration is changing."
        )

    if resource.action == ChangeAction.CREATE:
        return ChangeRisk(resource.id, RiskLevel.LOW, "New resource is being created.")

    return ChangeRisk(resource.id, RiskLevel.LOW, "No significant risk detected.")


def classify_all(resources: list[Resource], contract: Contract) -> list[ChangeRisk]:
    return [classify_change(r, contract) for r in resources]


def requires_human_approval(risks: list[ChangeRisk], contract: Contract) -> bool:
    if not contract.agent.destructive_changes.require_human_approval:
        return False
    return any(r.level == RiskLevel.CRITICAL for r in risks)
