# Using infra-contract as a GitHub Action

Drop this into a workflow in the repository whose Terraform/OpenTofu you want
to validate. It runs on every pull request, posts a summary comment, and
fails the check when a violation at or above `fail-on` is found.

`.github/workflows/infra-contract.yml` in the _consumer_ repo:

```yaml
name: Infra Contract

on:
  pull_request:
    paths:
      - "**/*.tf"
      - "infra-contract.yaml"

permissions:
  contents: read
  pull-requests: write # required only if comment-on-pr stays "true"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Generate plan
        run: |
          terraform init -input=false
          terraform plan -out=tfplan -input=false
          terraform show -json tfplan > plan.json

      - name: Validate infrastructure
        uses: khaleddeissa/infra-contract@v0.1.0
        with:
          contract: infra-contract.yaml
          plan: plan.json
          fail-on: high
          comment-on-pr: "true"
```

## Inputs reference

| Input               | Default               | Notes                                                                                              |
| ------------------- | --------------------- | -------------------------------------------------------------------------------------------------- |
| `contract`          | `infra-contract.yaml` | Path relative to `working-directory`.                                                              |
| `plan`              | _(empty)_             | If omitted, falls back to a lower-confidence scan of `.tf` source in `target`. Prefer a real plan. |
| `target`            | `.`                   | Directory scanned when no `plan` is given.                                                         |
| `fail-on`           | `high`                | One of `info \| warning \| medium \| high \| critical`.                                            |
| `working-directory` | `.`                   | Where the action runs.                                                                             |
| `comment-on-pr`     | `true`                | Requires `pull-requests: write`.                                                                   |

## Outputs

- `status` — `"passed"` or `"failed"`
- `score` — contract score out of 100, usable in a badge or downstream gate:

```yaml
- name: Validate infrastructure
  id: contract
  uses: khaleddeissa/infra-contract@v0.1.0
  with:
    plan: plan.json

- name: Fail deploy on low score
  if: steps.contract.outputs.status == 'failed'
  run: exit 1
```

The action also uploads `infra-contract-results.json` as a workflow artifact
on every run (pass or fail) for later inspection or downstream tooling.
