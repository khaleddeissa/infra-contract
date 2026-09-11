from __future__ import annotations

from pathlib import Path

from infra_contract.ir.model import ChangeAction, ResourceKind
from infra_contract.providers.terraform.provider import TerraformProvider

FIXTURE = Path(__file__).parent / "fixtures" / "sample_plan.json"


def test_normalizes_db_instance_to_database_kind():
    doc = TerraformProvider().load(FIXTURE)
    db = next(r for r in doc.resources if r.id == "aws_db_instance.production")
    assert db.kind == ResourceKind.DATABASE
    assert db.network.public is True
    assert db.reliability.multi_az is False
    assert db.action == ChangeAction.CREATE
    assert db.is_production()


def test_normalizes_iam_policy_wildcard():
    doc = TerraformProvider().load(FIXTURE)
    policy = next(r for r in doc.resources if r.id == "aws_iam_policy.application")
    assert policy.kind == ResourceKind.IAM
    assert policy.security.wildcard_permissions is True


def test_unmodeled_resource_types_are_skipped_not_guessed():
    """Providers must not fabricate an opinion about resource types they
    don't understand; they should simply omit them from the IR."""
    plan = {
        "resource_changes": [
            {
                "address": "aws_cloudfront_distribution.cdn",
                "type": "aws_cloudfront_distribution",
                "change": {"actions": ["create"], "after": {}},
            }
        ]
    }
    doc = TerraformProvider().normalize(plan)
    assert doc.resources == []
