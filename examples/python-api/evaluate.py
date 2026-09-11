"""Programmatic use of infra-contract, without going through the CLI.

Useful when embedding validation in custom tooling — e.g. a pre-deploy hook,
a bot, or a script that needs the structured result rather than CLI output.

Run from a checkout of a plan file:

    python examples/python-api/evaluate.py path/to/plan.json path/to/infra-contract.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

from contracts.loader import load_contract
from engine.evaluator import Evaluator
from providers.terraform.provider import TerraformProvider


def evaluate(plan_path: str, contract_path: str) -> int:
    contract = load_contract(contract_path)

    provider = TerraformProvider()
    document = provider.load(Path(plan_path))

    result = Evaluator().run(document, contract)

    print(f"status: {result.status}")
    print(f"score:  {result.score}/100")

    for finding in result.failed_findings:
        print(f"  [{finding.severity}] {finding.resource_id}: {finding.message}")

    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    plan_arg, contract_arg = sys.argv[1], sys.argv[2]
    sys.exit(evaluate(plan_arg, contract_arg))
