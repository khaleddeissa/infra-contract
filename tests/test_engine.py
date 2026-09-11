from __future__ import annotations

from pathlib import Path

from contracts.models import Contract, ProjectConfig
from engine.evaluator import Evaluator
from ir.model import ChangeAction, InfrastructureDocument, Resource, ResourceKind
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


def test_resource_in_disallowed_region_is_flagged():
    """Edge case: a resource with no region restriction violation elsewhere
    can still fail purely on `cloud.regions`, and a resource with no region
    at all (region=None) must be silently skipped rather than treated as a
    violation, since `applies_to` only matches when a region is known."""
    contract = _contract()
    contract.cloud.regions_allowed = ["eu-central-1"]

    document = InfrastructureDocument(
        source="test",
        resources=[
            Resource(
                id="aws_lambda_function.drifted",
                kind=ResourceKind.COMPUTE,
                provider="aws",
                resource_type="aws_lambda_function",
                region="us-east-1",  # not in the allow-list: drift
                action=ChangeAction.CREATE,
            ),
            Resource(
                id="aws_lambda_function.unregioned",
                kind=ResourceKind.COMPUTE,
                provider="aws",
                resource_type="aws_lambda_function",
                region=None,  # unknown region: policy must not guess
                action=ChangeAction.CREATE,
            ),
        ],
    )
    result = Evaluator().run(document, contract)

    region_findings = {
        f.resource_id: f for f in result.findings if f.rule == "architecture.approved-region-only"
    }
    assert region_findings["aws_lambda_function.drifted"].passed is False
    assert "aws_lambda_function.unregioned" not in region_findings


def test_unmodeled_resources_do_not_dilute_or_block_evaluation():
    """Edge case: a plan mixing a modeled violation with resource types the
    provider does not understand must still surface the modeled violation,
    and the unmodeled resources must contribute zero findings (no silent
    pass, no fabricated failure)."""
    contract = _contract()
    plan = {
        "resource_changes": [
            {
                "address": "aws_iam_policy.application",
                "type": "aws_iam_policy",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "policy": (
                            '{"Version":"2012-10-17","Statement":'
                            '[{"Effect":"Allow","Action":"*","Resource":"*"}]}'
                        )
                    },
                },
            },
            {
                "address": "aws_cloudfront_distribution.cdn",
                "type": "aws_cloudfront_distribution",
                "change": {"actions": ["create"], "after": {}},
            },
            {
                "address": "aws_sqs_queue.jobs",
                "type": "aws_sqs_queue",
                "change": {"actions": ["create"], "after": {}},
            },
        ]
    }
    document = TerraformProvider().normalize(plan)
    result = Evaluator().run(document, contract)

    assert len(document.resources) == 1  # only the IAM policy was modeled
    assert any(f.rule == "security.no-wildcard-iam" and not f.passed for f in result.findings)
    assert not any(
        f.resource_id in ("aws_cloudfront_distribution.cdn", "aws_sqs_queue.jobs")
        for f in result.findings
    )
