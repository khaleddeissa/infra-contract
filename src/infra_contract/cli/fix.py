from __future__ import annotations

from rich.console import Console

from infra_contract.cli.common import build_document, load_contract_or_exit
from infra_contract.engine.evaluator import Evaluator

console = Console()

# Very small, conservative set of "known good" one-line remediations we can
# render as a suggested diff. This intentionally does NOT touch any files —
# V1 only ever prints a suggestion, per the project design principle that
# infra-contract must not silently rewrite infrastructure.
_SUGGESTED_DIFFS = {
    "security.no-public-database": ("publicly_accessible = true", "publicly_accessible = false"),
    "security.no-public-storage": ('acl = "public-read"', 'acl = "private"'),
    "security.encryption-required": ("storage_encrypted = false", "storage_encrypted = true"),
    "reliability.production-backups": ("backup_retention_period = 0", "backup_retention_period = 7"),
    "reliability.production-multi-az": ("multi_az = false", "multi_az = true"),
}


def run_fix(
    target: str | None = None,
    contract_path: str | None = None,
    plan_path: str | None = None,
) -> None:
    contract = load_contract_or_exit(contract_path)
    document = build_document(plan_path=plan_path, target=target)

    evaluator = Evaluator()
    result = evaluator.run(document, contract)

    suggestions = [f for f in result.failed_findings if f.rule in _SUGGESTED_DIFFS]
    if not suggestions:
        console.print(
            "[green]No auto-suggestable fixes.[/green] Run `infra-contract explain` for "
            "remediation guidance on remaining findings."
        )
        return

    console.print("[bold]Suggested changes:[/bold]\n")
    for finding in suggestions:
        before, after = _SUGGESTED_DIFFS[finding.rule]
        console.print(f"[dim]# {finding.resource_id} — {finding.rule}[/dim]")
        console.print(f"[red]- {before}[/red]")
        console.print(f"[green]+ {after}[/green]\n")

    console.print(
        "These are suggestions only. infra-contract does not modify Terraform files "
        "or apply infrastructure automatically."
    )
