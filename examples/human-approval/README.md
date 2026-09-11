# Requiring human approval for destructive changes

`production-service/infra-contract.yaml` already sets:

```yaml
agent:
  production_apply: false
  destructive_changes:
    require_human_approval: true
```

This example walks through what that actually does end to end, since it's
easy to set the flag and never see it trigger.

1. Produce a plan that includes a destructive or replacing change (e.g. an
   RDS instance being replaced due to an immutable attribute change):
   ```bash
   terraform plan -out=tfplan
   terraform show -json tfplan > plan.json
   ```
2. Inspect just the contract-relevant changes first:
   ```bash
   infra-contract diff plan.json --contract examples/production-service/infra-contract.yaml
   ```
   This lists creates/updates/deletes/replacements the contract cares about
   without evaluating pass/fail — useful as a pre-review step.
3. Run the actual evaluation:
   ```bash
   infra-contract plan plan.json --contract examples/production-service/infra-contract.yaml
   ```
   When `destructive_changes.require_human_approval` is `true` and the plan
   contains a `delete` or `replace` action on a stateful resource (e.g. a
   database), the command reports it as a blocking finding regardless of
   `fail_on` severity — an AI agent or automated pipeline cannot silently
   apply it.
4. In an agent-driven workflow (see `examples/mcp-client`), this is the
   mechanism that keeps `infra_contract_validate_change` from waving through
   an autonomous destructive apply — the agent gets the finding back and
   must surface it to a human instead of proceeding.

Set `require_human_approval: false` only for environments where destructive
changes are expected and already reviewed elsewhere (e.g. ephemeral/dev).
