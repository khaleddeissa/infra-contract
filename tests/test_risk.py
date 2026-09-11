from __future__ import annotations

from contracts.models import Contract, ProjectConfig
from engine.risk import RiskLevel, classify_change, requires_human_approval
from ir.model import ChangeAction, Resource, ResourceKind


def _contract() -> Contract:
    return Contract(project=ProjectConfig(name="demo"))


def test_stateful_deletion_is_critical_and_requires_approval():
    resource = Resource(
        id="aws_db_instance.production",
        kind=ResourceKind.DATABASE,
        provider="aws",
        resource_type="aws_db_instance",
        action=ChangeAction.DELETE,
    )
    risk = classify_change(resource, _contract())

    assert risk.level == RiskLevel.CRITICAL
    assert requires_human_approval([risk], _contract())


def test_network_change_is_high_risk_but_not_a_destructive_block():
    resource = Resource(
        id="aws_security_group.api",
        kind=ResourceKind.NETWORK,
        provider="aws",
        resource_type="aws_security_group",
        action=ChangeAction.UPDATE,
    )
    risk = classify_change(resource, _contract())

    assert risk.level == RiskLevel.HIGH
    assert not requires_human_approval([risk], _contract())
