from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from cli.common import build_document, load_contract_or_exit
from engine.evaluator import Evaluator
from engine.risk import classify_all, requires_human_approval

console = Console()


def run_plan(plan_path: str, contract_path: str | None = None, output_format: str = "text") -> int:
    contract = load_contract_or_exit(contract_path)
    document = build_document(plan_path=plan_path)

    evaluator = Evaluator()
    eval_result = evaluator.run(document, contract)
    risks = classify_all(document.resources, contract)
    blocked = requires_human_approval(risks, contract)

    if output_format == "json":
        payload = eval_result.to_dict()
        payload["risks"] = [r.to_dict() for r in risks]
        payload["blocked"] = blocked or eval_result.status == "failed"
        console.print_json(json.dumps(payload))
        return 1 if payload["blocked"] else 0

    table = Table(title="Change Risk Analysis")
    table.add_column("Resource")
    table.add_column("Action")
    table.add_column("Risk")
    table.add_column("Reason")

    risk_by_resource = {r.resource_id: r for r in risks}
    for resource in document.resources:
        risk = risk_by_resource[resource.id]
        color = {"low": "green", "medium": "yellow", "high": "red", "critical": "bold red"}[
            risk.level.value
        ]
        table.add_row(
            resource.id,
            resource.action.value,
            f"[{color}]{risk.level.value.upper()}[/{color}]",
            risk.reason,
        )

    console.print(table)
    console.print(f"\nContract score: [bold]{eval_result.score}/100[/bold]")

    if blocked:
        console.print(
            "\n[bold red]Deployment blocked:[/bold red] a destructive change to a stateful "
            "resource requires human approval (agent.destructive_changes.require_human_approval)."
        )
    if eval_result.status == "failed":
        console.print(
            "[bold red]Contract violations detected — see `infra-contract explain`.[/bold red]"
        )

    return 1 if (blocked or eval_result.status == "failed") else 0


def run_diff(plan_path: str, contract_path: str | None = None) -> None:
    """Show only the contract-relevant changes in a plan (a thin view over `plan`)."""
    contract = load_contract_or_exit(contract_path)
    document = build_document(plan_path=plan_path)
    risks = classify_all(document.resources, contract)

    console.print("[bold]Infrastructure Contract Diff[/bold]\n")
    for resource, risk in zip(document.resources, risks):
        symbol = {"create": "+", "update": "~", "delete": "-", "replace": "±", "no-op": " "}[
            resource.action.value
        ]
        console.print(
            f"{symbol} {resource.resource_type} ({resource.id})  [dim]{risk.level.value}[/dim]"
        )
