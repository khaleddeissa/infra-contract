from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()
FIXTURE = Path(__file__).parent / "fixtures" / "sample_plan.json"


def test_init_creates_expected_files(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "infra-contract.yaml").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".github" / "workflows" / "infra-contract.yml").exists()


def test_check_fails_on_public_database(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(
        app,
        ["check", "--contract", str(tmp_path / "infra-contract.yaml"), "--plan", str(FIXTURE)],
    )
    assert result.exit_code == 1
    assert "critical" in result.stdout.lower()


def test_check_json_output_is_valid_json(tmp_path):
    import json

    runner.invoke(app, ["init", str(tmp_path)])
    result = runner.invoke(
        app,
        [
            "check",
            "--contract",
            str(tmp_path / "infra-contract.yaml"),
            "--plan",
            str(FIXTURE),
            "--format",
            "json",
        ],
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert any(v["rule"] == "security.no-public-database" for v in payload["violations"])


def test_plan_blocks_on_destructive_change(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    destructive_plan = tmp_path / "destroy.json"
    destructive_plan.write_text("""
{
  "resource_changes": [
    {
      "address": "aws_db_instance.production",
      "type": "aws_db_instance",
      "change": {"actions": ["delete"], "before": {"engine": "postgres", "tags": {"Environment": "production"}}}
    }
  ]
}
""")
    result = runner.invoke(
        app,
        ["plan", str(destructive_plan), "--contract", str(tmp_path / "infra-contract.yaml")],
    )
    assert result.exit_code == 1
    assert "blocked" in result.stdout.lower()
