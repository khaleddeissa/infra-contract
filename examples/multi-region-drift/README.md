# Edge case: silent region drift

`cloud.regions` is easy to set and easy to forget about — nothing stops a
module default, a provider alias, or a copy-pasted resource block from
deploying into a region the contract never approved. This example is the
smallest possible reproduction of that drift.

The contract only approves `eu-central-1`:

```yaml
cloud:
  provider: aws
  regions: [eu-central-1]
```

If a plan contains a resource created in any other region (for example
`us-east-1`), `architecture.approved-region-only` fails for that resource,
even though nothing else about it is wrong:

```bash
infra-contract check --plan tfplan.json --contract examples/multi-region-drift/infra-contract.yaml
```

Two related edge cases worth knowing about:

- **A resource with no region at all is skipped, not flagged.** The policy
  only applies when Terraform reports a `region` attribute, so resources the
  provider can't determine a region for (or global resources like some IAM
  types) never produce a false failure.
- **An empty `regions` list means "no restriction."** `regions: []` — or
  omitting `cloud.regions` entirely — disables this policy rather than
  failing every resource, so an incomplete contract fails open on region
  instead of failing closed.

This is a `medium` severity finding by default; raise `ci.fail_on` to
include `medium` (as above) if region drift alone should block a merge.
