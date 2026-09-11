from __future__ import annotations

from ai import generate_agent_instructions
from contracts import Contract, ProjectConfig, Severity
from engine import Evaluator, Finding
from ir import InfrastructureDocument
from policies import ALL_BUILTIN_POLICIES
from providers import TerraformProvider


def test_top_level_packages_expose_reusable_public_api():
    contract = Contract(project=ProjectConfig(name="demo"))
    instructions = generate_agent_instructions(contract)

    assert "infra-contract" in instructions
    assert ALL_BUILTIN_POLICIES
    assert isinstance(TerraformProvider().name, str)


def test_evaluator_can_evaluate_an_empty_document():
    result = Evaluator().run(
        InfrastructureDocument(source="test"), Contract(project={"name": "demo"})
    )

    assert result.status == "passed"
    assert result.score == 100


def test_finding_serializes_severity_as_json_value():
    finding = Finding(
        rule="test.rule",
        severity=Severity.HIGH,
        resource_id="resource.test",
        category="test",
        message="Example",
        passed=False,
    )

    assert finding.to_dict()["severity"] == "high"
