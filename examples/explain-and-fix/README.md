# Explaining and fixing violations

Once `check` reports a failure, use `explain` for a human-readable
breakdown, and `fix` to see a suggested patch — it never applies anything on
its own.

```bash
# Full human-readable breakdown of every violation
infra-contract explain --contract infra-contract.yaml path/to/terraform

# Narrow to a single resource
infra-contract explain --resource aws_s3_bucket.data --contract infra-contract.yaml path/to/terraform

# Same options work against a plan instead of source
infra-contract explain --plan plan.json --contract infra-contract.yaml

# Suggested patches for known-fixable violations
infra-contract fix --contract infra-contract.yaml path/to/terraform
```

`fix` only proposes changes for violation types it has a known-safe patch
for (e.g. enabling default encryption, removing a public-access flag) — it
prints a suggested diff for you to review and apply, and intentionally never
writes to your `.tf` files itself.
