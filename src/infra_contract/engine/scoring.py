from __future__ import annotations

from infra_contract.contracts.models import Severity
from infra_contract.engine.findings import Finding

# Points deducted per failed finding, by severity. A score is a *summary*,
# never the primary signal — a CRITICAL finding must always surface on its
# own regardless of the aggregate score (see engine/evaluator.py).
_PENALTY = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 12,
    Severity.MEDIUM: 6,
    Severity.WARNING: 3,
    Severity.INFO: 0,
}


def compute_score(findings: list[Finding]) -> int:
    score = 100
    for finding in findings:
        if not finding.passed:
            score -= _PENALTY.get(finding.severity, 5)
    return max(0, min(100, score))


def compute_category_scores(findings: list[Finding]) -> dict[str, int]:
    by_category: dict[str, list[Finding]] = {}
    for finding in findings:
        by_category.setdefault(finding.category, []).append(finding)
    return {category: compute_score(items) for category, items in by_category.items()}
