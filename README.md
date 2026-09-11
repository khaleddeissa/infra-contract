# infra-contract

<p align="center">
  <img src="assets/logo.svg" alt="infra-contract logo" height="140">
</p>

<h1 align="center">infra-contract</h1>

<p align="center">
  Version-controlled infrastructure rules for people, CI, and AI agents.
</p>

<p align="center">
  <code>infra-contract</code> evaluates Terraform/OpenTofu infrastructure against a small,
  reviewable YAML contract. It gives humans and agents the same answer before a change is
  merged or deployed.
</p>

[![CI](https://github.com/khaleddeissa/infra-contract/actions/workflows/ci.yml/badge.svg?branch=main&style=for-the-badge)](https://github.com/khaleddeissa/infra-contract/actions/workflows/ci.yml)
[![Security](https://img.shields.io/badge/Security-CodeQL%20%26%20Dependency%20Review-2EA44F?style=for-the-badge&logo=github&logoColor=white)](https://github.com/khaleddeissa/infra-contract/actions/workflows/security.yml)
[![Latest release](https://img.shields.io/github/v/release/khaleddeissa/infra-contract?display_name=tag&sort=semver&style=for-the-badge)](https://github.com/khaleddeissa/infra-contract/releases)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Terraform](https://img.shields.io/badge/Terraform%20%2F%20OpenTofu-Plan%20Validation-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://developer.hashicorp.com/terraform)
[![MCP](https://img.shields.io/badge/Model%20Context%20Protocol-MCP-000000?style=for-the-badge&logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-Apache--2.0-0D75B8?style=for-the-badge)](LICENSE)

## Architecture

<img width="5971" height="3334" alt="Infra_Contract_Flow" src="https://github.com/user-attachments/assets/174a1715-e8f5-43ce-a81d-27d26bb48de1" />

Valid Terraform can still create public databases, overly broad IAM policies,
unsupported architecture, or risky destructive changes. That gap becomes more
important when AI agents generate infrastructure. This project makes the rules
explicit, machine-readable, and independently enforced.

```text
    Developer or AI agent
             |
             v
    Terraform / OpenTofu change
             |
             v
    +------------------------+
    |  infra-contract.yaml   |
    |  policy engine         |
    +------------------------+
        |               |
        v               v
    CLI / MCP          CI gate
        \               /
         +-- deployment decision --+
```

## Features

- YAML contracts validated with Pydantic.
- Terraform/OpenTofu plan parsing, plus a lower-confidence source scan.
- Built-in security, networking, reliability, and architecture policies.
- CLI, Python API, MCP server, and a reusable GitHub Action using one engine.
- Change-risk reporting and optional human approval for destructive stateful changes.
- JSON output suitable for CI and agent tooling.

## Install

Requires Python 3.10+.

```bash
uv tool install infra-contract
# or
pip install infra-contract
```

To work from a checkout:

```bash
uv sync --all-extras
uv run infra-contract --help
```

## Quick start

Initialize a repository, then review the generated contract before relying on it.

```bash
cd my-infrastructure-repository
infra-contract init
infra-contract check
```

Use an actual plan for the highest-confidence validation:

```bash
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
infra-contract check --plan tfplan.json
infra-contract plan tfplan.json
```

For scripts and CI, use JSON and set the blocking severity explicitly:

```bash
infra-contract check --plan tfplan.json --format json --fail-on high
```

## Contract reference

```yaml
version: "1"
project:
  name: my-service
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
ci:
  fail_on: [high, critical]
```

See [basic-terraform](examples/basic-terraform),
[production-service](examples/production-service), and
[rag-app](examples/rag-app) for complete starting points.

## Interfaces

### CLI

```bash
infra-contract init [PROJECT_ROOT]
infra-contract check [TARGET] [--contract PATH] [--plan PLAN.json] [--format text|json]
infra-contract plan PLAN.json [--contract PATH]
infra-contract diff PLAN.json [--contract PATH]
infra-contract explain [--resource RESOURCE_ID] [--plan PLAN.json]
infra-contract fix [TARGET] [--plan PLAN.json]
infra-contract mcp [--contract PATH]
```

`check` returns exit code `1` for blocking findings. `plan` also reports risk;
a deletion or replacement of a database, cache, or storage resource is critical
when the contract requires human approval. `fix` only proposes changes—it never
modifies infrastructure.

### Python

The flattened source layout intentionally exposes reusable packages directly:

```python
from contracts import Contract, load_contract
from engine import Evaluator
from providers import TerraformProvider

contract = load_contract("infra-contract.yaml")
document = TerraformProvider().load("tfplan.json")
result = Evaluator().run(document, contract)
print(result.to_dict())
```

Public API packages are `ai`, `cli`, `contracts`, `engine`, `ir`, `mcp`,
`policies`, and `providers`. Their `__init__.py` files expose the intended
reusable symbols; import implementation modules only when you need a
specialized type.

### MCP for AI agents

Run the server over stdio:

```bash
infra-contract mcp --contract infra-contract.yaml
```

The server offers contract discovery, policy lookup, source/plan validation,
violation explanation, single-resource preflight checks, and change-risk
analysis. It does not apply infrastructure. See [the MCP example](examples/mcp-client).

### GitHub Actions

The repository itself is a composite action. Pin a tag or commit SHA in a
consumer workflow:

```yaml
name: Infrastructure contract
on: [pull_request]
permissions:
  contents: read
  pull-requests: write # only needed when comment-on-pr is true

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: OWNER/infra-contract@v0.1.0
        with:
          plan: tfplan.json
          fail-on: high
          comment-on-pr: true
```

The generated workflow from `infra-contract init` is a simple CLI-based
alternative. This repository also includes CI, dependency review, and CodeQL
workflows.

## Docker and Compose

The image is a multi-stage build, uses a locked `uv` environment, and runs as a
non-root user. It is intentionally a CLI image, so it has no HTTP port or
healthcheck.

```bash
docker build -t infra-contract:local .
docker run --rm -v "$PWD:/workspace:ro" -w /workspace infra-contract:local \
  check --contract examples/rag-app/infra-contract.yaml examples/rag-app

docker compose build
docker compose run --rm infra-contract check \
  --contract examples/production-service/infra-contract.yaml path/to/terraform
```

## Development

```bash
uv sync --all-extras
uv run isort --check-only src tests
uv run black --check src tests
uv run mypy src
uv run pytest -v
```

Apply local formatting with `uv run isort src tests` and `uv run black src tests`.
The project intentionally uses Black and isort rather than Ruff for formatting
and import ordering.

Convenience targets mirror CI:

```bash
make install
make check
make ci
make hooks-install
```

The pre-commit hook checks file hygiene, YAML/TOML, import ordering, and Black
on commits; mypy and pytest run on push. The included `.pre-commit-hooks.yaml`
also lets downstream repositories install `infra-contract check` as a reusable
hook.

## Repository layout

```text
src/
├── contracts/  # YAML schema and loader
├── ir/         # provider-neutral infrastructure model
├── policies/   # policy primitives and built-in rules
├── engine/     # evaluation, scoring, risk
├── providers/  # Terraform/OpenTofu adapters
├── cli/        # Typer commands
├── mcp/        # MCP server
└── ai/         # generated agent instructions
```

The dependency flow is one way: providers normalize into `ir`; policies and the
engine evaluate `contracts` plus `ir`; CLI/MCP/action only transport results.
Architecture tests prevent core packages from importing interface layers.

## Security and release

GitHub Actions runs tests, Black, isort, mypy, package builds, dependency review
on pull requests, and scheduled CodeQL analysis. Enable Dependabot and GitHub
Advanced Security features in repository settings where available.

To publish the GitHub Action in Marketplace, first create a versioned release:

1. Confirm CI is green and update the version/changelog as appropriate.
2. Create and push an annotated tag such as `v0.1.0`; the release workflow builds
   and publishes the Python package if PyPI Trusted Publishing is configured.
3. Open GitHub **Releases** → **Draft a new release**, choose that tag, add release
   notes, and publish it.
4. GitHub will then offer Marketplace publication. Review the listing metadata,
   confirm the action is safe for public use, and publish the listing.

Do not click “Draft a release” until the tag/version and PyPI trusted-publisher
configuration are ready. Marketplace publication is optional; users can always
reference `OWNER/infra-contract@v0.1.0` directly.

`Dockerfile.goreleaser` is intentionally not included. GoReleaser builds and
releases Go programs; this project publishes a Python package and a Docker CLI
image through `uv` and the existing release workflow.

## Scope

`infra-contract` is a validation layer, not Terraform, a cloud deployment
platform, or an autonomous apply tool. Policies only cover modeled resource types;
an unknown resource produces no opinion, so pair this with cloud-native controls
and code review.

## License

[Apache-2.0](LICENSE)
