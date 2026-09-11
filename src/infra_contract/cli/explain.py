from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from infra_contract.cli.common import build_document, load_contract_or_exit
from infra_contract.engine.evaluator import Evaluator

console = Console()


def run_explain(
    resource_id: str | None = None,
    target: str | None = None,
    contract_path: str | None = None,
    plan_path: str | None = None,
) -> None:
    contract = load_contract_or_exit(contract_path)
    document = build_document(plan_path=plan_path, target=target)

    evaluator = Evaluator()
    result = evaluator.run(document, contract)
    findings = evaluator.explain(result, resource_id=resource_id)

    if not findings:
        console.print("[green]No contract violations found.[/green]")
        return

    for finding in findings:
        body = (
            f"[bold]Resource:[/bold]\n{finding.resource_id}\n\n"
            f"[bold]Violation:[/bold]\n{finding.message}\n\n"
            f"[bold]Contract:[/bold]\n{finding.rule}\n\n"
        )
        if finding.expected is not None:
            body += f"[bold]Expected:[/bold]\n{finding.expected}\n\n"
        if finding.actual is not None:
            body += f"[bold]Detected:[/bold]\n{finding.actual}\n\n"
        if finding.remediation:
            body += f"[bold]Recommended remediation:[/bold]\n{finding.remediation}"

        console.print(
            Panel(
                body.strip(),
                title=f"[red]{finding.severity.value.upper()}[/red]",
                border_style="red" if finding.severity.value in ("critical", "high") else "yellow",
            )
        )
