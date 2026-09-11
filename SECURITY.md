# Security Policy

## Supported Versions

`infra-contract` is currently pre-1.0 and released as a single active line.
Only the **latest published release** on [PyPI](https://pypi.org/project/infra-contract/)
and the corresponding [GitHub Release](https://github.com/khaleddeissa/infra-contract/releases)
receives security fixes. There is no long-term-support branch at this stage.

| Version        | Supported |
| -------------- | --------- |
| Latest release | ✅        |
| Older releases | ❌        |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately using one of the following:

- [GitHub Security Advisories](https://github.com/khaleddeissa/infra-contract/security/advisories/new) (preferred)
- Email: khaledayman012@gmail.com

When reporting, please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a minimal proof-of-concept
- The affected version(s)

You should expect an initial response within **5 business days**. If the
issue is confirmed, a fix will be prioritized and a new release cut; you'll
be credited in the release notes unless you prefer to remain anonymous.

## Scope

This policy covers the `infra-contract` CLI, Python package, MCP server, and
the GitHub Action distributed from this repository (`ghcr.io/khaleddeissa/infra-contract`
container image included).

It does **not** cover:

- Vulnerabilities in Terraform/OpenTofu itself, or in cloud provider services
- Infrastructure that a contract fails to flag due to a resource type not
  yet modeled (see [Scope](README.md#scope) in the README) — that's a
  feature gap, not a security vulnerability, and should be reported as a
  regular issue instead

## Automated Checks

This repository runs [CodeQL](.github/workflows/security.yml) static
analysis and dependency review on every pull request and push to `main`.
Dependabot keeps dependencies current via automated update PRs.
