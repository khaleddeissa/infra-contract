# Quickstart: generating your first contract

If you don't have an `infra-contract.yaml` yet, don't hand-write one — let
`init` detect your project and generate a starting point.

```bash
cd path/to/your/terraform/project
infra-contract init .
```

This inspects the project root and writes an `infra-contract.yaml` scaffold
tailored to what it finds there. From here:

1. Open the generated `infra-contract.yaml` and adjust policies to match your
   actual requirements (start from `examples/basic-terraform` or
   `examples/production-service` for reference points at two different
   strictness levels).
2. Run a first check against it:
   ```bash
   infra-contract check --contract infra-contract.yaml .
   ```
3. Commit `infra-contract.yaml` to version control — it's meant to be
   reviewed and evolved in pull requests like any other config, which is the
   whole point of a _version-controlled_ contract.
4. Wire it into CI — see `examples/github-actions-consumer` for the GitHub
   Actions side, or run `infra-contract check --format json` directly in any
   other CI system.
