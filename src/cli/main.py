from __future__ import annotations

import typer

from cli.check import run_check
from cli.explain import run_explain
from cli.fix import run_fix
from cli.init_cmd import run_init
from cli.plan import run_diff, run_plan

app = typer.Typer(
    name="infra-contract",
    help="Infrastructure contracts for humans and AI agents.",
    no_args_is_help=True,
)


@app.command()
def init(project_root: str = typer.Argument(".", help="Path to the project root.")) -> None:
    """Detect the project and generate a starter contract."""
    run_init(project_root)


@app.command()
def check(
    target: str | None = typer.Argument(None, help="File or directory to validate."),
    contract: str | None = typer.Option(None, "--contract", help="Path to infra-contract.yaml."),
    plan: str | None = typer.Option(
        None, "--plan", help="Path to `terraform show -json` plan output."
    ),
    format: str = typer.Option("text", "--format", help="Output format: text or json."),
    fail_on: str | None = typer.Option(
        None,
        "--fail-on",
        help="Minimum severity that fails the command (overrides contract ci.fail_on).",
    ),
) -> None:
    """Validate infrastructure against the contract."""
    exit_code = run_check(
        target=target, contract_path=contract, plan_path=plan, output_format=format, fail_on=fail_on
    )
    raise typer.Exit(code=exit_code)


@app.command()
def explain(
    resource: str | None = typer.Option(None, "--resource", help="Limit to one resource id."),
    target: str | None = typer.Argument(None),
    contract: str | None = typer.Option(None, "--contract"),
    plan: str | None = typer.Option(None, "--plan"),
) -> None:
    """Human-readable explanation of each violation."""
    run_explain(resource_id=resource, target=target, contract_path=contract, plan_path=plan)


@app.command()
def plan(
    plan_file: str = typer.Argument(..., help="Path to `terraform show -json` plan output."),
    contract: str | None = typer.Option(None, "--contract"),
    format: str = typer.Option("text", "--format"),
) -> None:
    """Evaluate a Terraform/OpenTofu plan, including change-risk analysis."""
    exit_code = run_plan(plan_file, contract_path=contract, output_format=format)
    raise typer.Exit(code=exit_code)


@app.command()
def diff(
    plan_file: str = typer.Argument(..., help="Path to `terraform show -json` plan output."),
    contract: str | None = typer.Option(None, "--contract"),
) -> None:
    """Show contract-relevant infrastructure changes in a plan."""
    run_diff(plan_file, contract_path=contract)


@app.command()
def fix(
    target: str | None = typer.Argument(None),
    contract: str | None = typer.Option(None, "--contract"),
    plan: str | None = typer.Option(None, "--plan"),
) -> None:
    """Generate suggested patches for known-fixable violations (never auto-applies)."""
    run_fix(target=target, contract_path=contract, plan_path=plan)


@app.command()
def mcp(
    contract: str | None = typer.Option(None, "--contract", help="Path to infra-contract.yaml."),
) -> None:
    """Start the MCP server, exposing this same engine to AI agents over stdio."""
    from mcp.server import serve

    serve(contract_path=contract)


if __name__ == "__main__":
    app()
