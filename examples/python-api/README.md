# Python API

Every entry point in this project — CLI, GitHub Action, MCP server — calls
the same underlying engine:

```
Contract + InfrastructureDocument -> Evaluator.run() -> EvaluationResult
```

`evaluate.py` in this folder shows the minimal version of that pipeline
directly in Python:

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
python examples/python-api/evaluate.py plan.json examples/basic-terraform/infra-contract.yaml
```

Use this when you need the structured `EvaluationResult` object (score,
per-finding severity, `.to_dict()` for JSON) inside custom tooling, rather
than parsing CLI stdout. `result.failures_at_or_above(Severity.HIGH)` is
useful if you want your own custom gating logic instead of `--fail-on`.
