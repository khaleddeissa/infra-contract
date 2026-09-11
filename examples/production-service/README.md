# Production service contract

Use this as a stricter starting point for an ECS + RDS production workload. It
requires private, encrypted, highly available databases and blocks wildcard IAM
permissions.

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
infra-contract plan plan.json --contract examples/production-service/infra-contract.yaml
```

The `plan` command adds change-risk output and blocks destructive stateful changes
when human approval is required by the contract.
