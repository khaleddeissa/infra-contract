# Running infra-contract in Docker

Useful when you'd rather not install Python/uv locally, or want an isolated
environment for CI runners that don't already have Python set up.

Build once:

```bash
docker compose build
```

Then run any CLI command by passing it as the compose command, mounting your
project directory read-only:

```bash
docker compose run --rm infra-contract check \
  --contract examples/rag-app/infra-contract.yaml \
  examples/rag-app
```

Against your own project instead of the bundled examples, mount it in place
of the repo checkout:

```bash
docker run --rm \
  -v "$(pwd)":/workspace:ro \
  -w /workspace \
  infra-contract:local \
  check --contract infra-contract.yaml .
```

The container mounts your project **read-only** by design — `fix` will
still print suggested patches, but writing them back means running that step
outside the container against your actual working tree.
