.DEFAULT_GOAL := help

.PHONY: help install format format-check test typecheck build check ci hooks-install hooks-run docker-build docker-check compose-check clean

help: ## Show available development commands.
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project and development dependencies with uv.
	uv sync --all-extras

format: ## Apply import ordering and Black formatting.
	uv run isort src tests
	uv run black src tests

format-check: ## Verify import ordering and formatting without modifying files.
	uv run isort --check-only src tests
	uv run black --check src tests

test: ## Run the pytest suite.
	uv run pytest -v

typecheck: ## Run mypy.
	uv run mypy

build: ## Build the source distribution and wheel.
	uv build

check: format-check typecheck test ## Run all source-quality checks.

ci: install check build ## Reproduce the main CI checks locally.

hooks-install: ## Install this repository's pre-commit hooks.
	uv run pre-commit install --install-hooks

hooks-run: ## Run every pre-commit hook against all files.
	uv run pre-commit run --all-files

docker-build: ## Build the local CLI container image.
	docker build --tag infra-contract:local .

docker-check: docker-build ## Smoke-test the local CLI container image.
	docker run --rm infra-contract:local --help

compose-check: ## Validate the Compose configuration.
	docker compose config

clean: ## Remove local Python build and test artifacts.
	rm -rf build dist .pytest_cache .mypy_cache .coverage coverage.xml
