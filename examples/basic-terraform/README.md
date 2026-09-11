# Basic Terraform contract

This is the smallest useful contract: Lambda and S3 are approved, while public or
unencrypted object storage is rejected.

```bash
infra-contract check --contract examples/basic-terraform/infra-contract.yaml path/to/terraform
```

For an authoritative pre-deploy check, generate a Terraform/OpenTofu plan and use
`infra-contract check --plan plan.json` instead of source scanning.
