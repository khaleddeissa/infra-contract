# RAG application contract

A contract for a retrieval-augmented-generation service: a vector store, an
embedding/inference compute layer, and the storage/networking around them. It
approves the managed services this kind of workload typically needs while
still rejecting public or unencrypted data stores.

```bash
infra-contract check --contract examples/rag-app/infra-contract.yaml path/to/terraform
```

As with the other examples, prefer a real plan for CI:

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
infra-contract check --plan plan.json --contract examples/rag-app/infra-contract.yaml
```
