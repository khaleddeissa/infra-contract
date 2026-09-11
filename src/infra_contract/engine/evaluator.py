"""
The Policy Engine
=================

This is the single engine that the CLI, the GitHub Action, and the MCP
server all call. None of them re-implement evaluation logic; they only
format and transport what this module produces.

    Contract + InfrastructureDocument -> Evaluator.run() -> EvaluationResult
"""

from __future__ import annotations

from pydantic import BaseModel

from infra_contract.contracts.models import Contract, Severity
from infra_contract.engine.findings import Finding
from infra_contract.engine.scoring import compute_category_scores, compute_score
from infra_contract.ir.model import InfrastructureDocument
from infra_contract.policies.base import Policy
from infra_contract.policies.builtin import ALL_BUILTIN_POLICIES


class EvaluationResult(BaseModel):
    score: int
    category_scores: dict[str, int]
    findings: list[Finding]
    status: str  # "passed" | "failed"

    @property
    def failed_findings(self) -> list[Finding]:
        return [f for f in self.findings if not f.passed]

    def failures_at_or_above(self, severity: Severity) -> list[Finding]:
        order = [Severity.INFO, Severity.WARNING, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        threshold = order.index(severity)
        return [f for f in self.failed_findings if order.index(f.severity) >= threshold]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "score": self.score,
            "category_scores": self.category_scores,
            "violations": [f.to_dict() for f in self.failed_findings],
        }


class Evaluator:
    """Evaluates a normalized infrastructure document against a Contract."""

    def __init__(self, policies: list[Policy] | None = None):
        self.policies = policies if policies is not None else list(ALL_BUILTIN_POLICIES)

    def _active_policies(self, contract: Contract) -> list[Policy]:
        return [p for p in self.policies if contract.is_policy_enabled(p.id)]

    def run(self, document: InfrastructureDocument, contract: Contract) -> EvaluationResult:
        findings: list[Finding] = []
        for policy in self._active_policies(contract):
            findings.extend(policy.run(document, contract))

        score = compute_score(findings)
        category_scores = compute_category_scores(findings)
        fail_on = set(contract.ci.fail_on)
        has_blocking_failure = any(
            not f.passed and f.severity in fail_on for f in findings
        )

        return EvaluationResult(
            score=score,
            category_scores=category_scores,
            findings=findings,
            status="failed" if has_blocking_failure else "passed",
        )

    def explain(self, result: EvaluationResult, resource_id: str | None = None) -> list[Finding]:
        failures = result.failed_findings
        if resource_id:
            failures = [f for f in failures if f.resource_id == resource_id]
        return failures
