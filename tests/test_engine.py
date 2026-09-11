from __future__ import annotations

from pathlib import Path

from contracts.models import Contract, ProjectConfig
from engine.evaluator import Evaluator
from providers.terraform.provider import TerraformProvider

FIXTURE = Path(__file__).parent / "fixtures" / "sample_plan.json"


def _contract(**overrides) -> Contract:
    base = {"project": ProjectConfig(name="test")}
    base.update(overrides)
    return Contract(**base)


def _document():
    return TerraformProvider().load(FIXTURE)


def test_public_database_is_critical_and_fails():
    contract = _contract()
    result = Evaluator().run(_document(), contract)

    critical = [f for f in result.failed_findings if f.severity.value == "critical"]
    assert any(f.rule == "security.no-public-database" for f in critical)
    assert result.status == "failed"


def test_wildcard_iam_detected():
    contract = _contract()
    result = Evaluator().run(_document(), contract)
    assert any(f.rule == "security.no-wildcard-iam" and not f.passed for f in result.findings)


def test_approved_ecs_compute_passes():
    contract = _contract()
    contract.architecture.compute.allowed = ["ecs"]
    result = Evaluator().run(_document(), contract)
    ecs_findings = [f for f in result.findings if f.resource_id == "aws_ecs_service.api"]
    assert all(f.passed for f in ecs_findings if f.rule == "architecture.approved-compute-only")


def test_score_never_masks_critical_findings():
    """A score can be non-zero, but a CRITICAL finding must still be present
    in the raw findings list — never hidden behind an aggregate number."""
    contract = _contract()
    result = Evaluator().run(_document(), contract)
    assert result.score < 100
    assert any(f.severity.value == "critical" for f in result.failed_findings)


def test_disabling_a_policy_removes_its_findings():
    contract = _contract()
    contract.policies.disabled = ["security.no-public-database"]
    result = Evaluator().run(_document(), contract)
    assert not any(f.rule == "security.no-public-database" for f in result.findings)


def test_fail_on_threshold_controls_pass_fail():
    contract = _contract()
    contract.ci.fail_on = []  # nothing blocks
    result = Evaluator().run(_document(), contract)
    assert result.status == "passed"
