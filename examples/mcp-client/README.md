# MCP client setup

Run the server over standard input/output from the repository whose infrastructure
you want to govern:

```bash
infra-contract mcp --contract infra-contract.yaml
```

Register that command in your MCP-capable AI client. The server exposes contract
discovery, policy lookup, source and plan validation, violation explanations, and
change-risk analysis. It never applies infrastructure.

Suggested agent sequence:

1. Call `infra_contract_get_contract` and `infra_contract_get_architecture`.
2. Call `infra_contract_validate_change` before writing a modeled resource.
3. Generate a real plan and call `infra_contract_check_plan` before proposing it.
