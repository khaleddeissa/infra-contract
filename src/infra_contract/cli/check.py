from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from infra_contract.cli.common import build_document, load_contract_or_exit
from infra_contract.contracts.models import Severity
from infra_contract.engine.evaluator import Evaluator

console = Console()


def run_check(
    target: str | None = None,
    contract_path: str | None = None,
    plan_path: str | None = None,
    output_format: str = "text",
    fail_on: str | None = None,
) -> int:
    """Runs the engine and returns a process exit code (0 pass, 1 fail)."""
    contract = load_contract_or_exit(contract_path)
    document = build_document(plan_path=plan_path, target=target)

    evaluator = Evaluator()
    result = evaluator.run(document, contract)

    threshold = Severity(fail_on) if fail_on else None
    blocking = (
        result.failures_at_or_above(threshold) if threshold else result.failed_findings
    )
    passed = result.status == "passed" if not threshold else len(blocking) == 0

    if output_format == "json":
        payload = result.to_dict()
        payload["status"] = "passed" if passed else "failed"
        console.print_json(json.dumps(payload))
    else:
        _render_text(result, document)

    return 0 if passed else 1


def _render_text(result, document) -> None:
    table = Table(title="infra-contract")
    table.add_column("Category")
    table.add_column("Result")

    for category, score in result.category_scores.items():
        failed = any(
            f.category == category and not f.passed for f in result.findings
        )
        has_critical = any(
            f.category == category and not f.passed and f.severity.value == "critical"
            for f in result.findings
        )
        if has_critical or (failed and score < 60):
            mark = "[red]✗ FAIL[/red]"
        elif failed:
            mark = "[yellow]⚠ WARNING[/yellow]"
        else:
            mark = "[green]✓ PASS[/green]"
        table.add_row(category.title(), mark)

    console.print(table)

    counts = {"critical": 0, "high": 0, "medium": 0, "warning": 0}
    for f in result.failed_findings:
        if f.severity.value in counts:
            counts[f.severity.value] += 1

    console.print()
    console.print(
        f"{counts['critical']} critical   {counts['high']} high   "
        f"{counts['medium']} medium   {counts['warning']} warnings"
    )
    console.print(f"\nContract score: [bold]{result.score}/100[/bold]")

    if result.failed_findings:
        console.print("\nRun [bold]infra-contract explain[/bold] for details.")
