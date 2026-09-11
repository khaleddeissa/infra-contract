# infra-contract

Infrastructure contracts for humans and AI agents.

Define what your infrastructure is allowed to do. Validate every
infrastructure change — human-written or AI-generated — against it.

```
                    Developer
                        │
                    AI Agent
                        │
                        ↓
               ┌─────────────────┐
               │  infra-contract │
               │                 │
               │ Architecture    │
               │ Security        │
               │ Cost            │
               │ Reliability     │
               │ Observability   │
               │ Agent Rules     │
               └─────────────────┘
                        │
                        ↓
                Infrastructure
                        │
                        ↓
                    Production
```

## Why

Infrastructure can be syntactically valid, deployable, and technically
functional while still violating the architecture, security, cost,
reliability, or operational requirements of a project. This gets worse as
AI coding agents increasingly generate Terraform, IAM, and cloud
infrastructure directly.

`infra-contract` gives developers, CI, and AI agents one version-controlled,
machine-readable contract to check against — instead of asking an agent to
infer an organization's infrastructure rules from scratch.

## Architecture

The engine is built around one dependency direction. Everything downstream
only ever talks to the engine — never to each other.

```
                ┌─────────────────┐
                │ Contract Models │   (contracts/)
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │ Policy Engine   │   (engine/, policies/)
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │ Normalized IR   │   (ir/)
                └────────┬────────┘
                         ↑
             ┌───────────┼───────────┐
             │           │           │
         Terraform      AWS      Kubernetes   (providers/, v2+)
             │
             ↓
      ┌────────────────┐
      │ CLI / MCP / CI │
      └────────────────┘
```

* **Contract Models** (`contracts/models.py`) are the only schema every other
  layer is allowed to depend on. Pydantic-validated, versioned, YAML-first.
* **Policy Engine** (`engine/evaluator.py`, `policies/`) evaluates a
  `Contract` against a normalized document. Policies never import a
  provider — they only see `ir.model.Resource`.
* **Normalized IR** (`ir/model.py`) is what makes multi-provider support
  practical: a Terraform `aws_db_instance`, a future Kubernetes
  `StatefulSet`, or a live AWS API scan all become the same `Resource`
  shape before a policy ever looks at them.
* **Providers** (`providers/terraform/`) are the only code that understands
  a native format (Terraform plan JSON in V1). They translate into IR and
  know nothing about policies.
* **CLI, MCP, GitHub Action** are thin consumers. They format and transport;
  they never re-implement evaluation. `infra-contract check`,
  `infra_contract_check_plan` (MCP), and the GitHub Action all call the
  exact same `Evaluator.run()`.

This is enforced, not just described: see `tests/test_architecture.py`,
which fails the build if `contracts/` or `engine/` ever import from
`providers/`, `cli/`, or `mcp/`.

## Install

```bash
uv tool install infra-contract
# or
pip install infra-contract
# or, project-local
uvx infra-contract init
```

## Quickstart

```bash
cd my-project
infra-contract init      # detects your stack, writes infra-contract.yaml,
                          # AGENTS.md / CLAUDE.md, and a GitHub Actions workflow
infra-contract check     # validates .tf source (best-effort, no plan needed)
```

For higher-confidence validation against what will actually be deployed:

```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
infra-contract check --plan tfplan.json
infra-contract plan tfplan.json      # + change-risk analysis
infra-contract explain               # human-readable remediation
```

Machine-readable output for CI/automation:

```bash
infra-contract check --format json --fail-on high
```

## AI agent integration

`infra-contract init` generates `AGENTS.md` / `CLAUDE.md` so any coding
agent gets explicit infrastructure rules as context instead of guessing.

An MCP server exposes the same engine as first-class tools:

```bash
infra-contract mcp
```

```
AI Agent: "I want to add a public S3 bucket."
      ↓
MCP → infra_contract_validate_change
      ↓
infra-contract engine → Contract evaluation
      ↓
DENIED — "Production object storage must not be publicly accessible."
```

The separation this creates is the point: **AI reasoning ≠ infrastructure
authority.** The agent can propose. The contract — evaluated independently,
outside the agent's own reasoning — determines whether the proposal
conforms. The same check runs again in CI on the final Terraform, so the
agent's own self-check can never be the only gate.

## Example contract

```yaml
version: "1"
project:
  name: my-rag-app
cloud:
  provider: aws
  regions: [eu-central-1]
architecture:
  compute:
    allowed: [ecs]
  database:
    allowed: [rds-postgres]
security:
  database:
    public_access: false
    encryption: required
  iam:
    wildcard_permissions: forbidden
reliability:
  production:
    backups: required
    multi_az: required
agent:
  production_apply: false
  destructive_changes:
    require_human_approval: true
```

## What this is not

`infra-contract` is not a Terraform replacement, a cloud provider, a
deployment platform, or an AI coding agent. It is a contract and validation
layer sitting between infrastructure code / AI agents and deployment.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy .
```

## License

Apache-2.0
