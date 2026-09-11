from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from contracts.models import Contract


class ContractLoadError(RuntimeError):
    def __init__(self, path: Path, errors: str):
        super().__init__(f"Invalid contract at {path}:\n{errors}")
        self.path = path
        self.errors = errors


def load_contract(path: str | Path) -> Contract:
    """Load and validate an infra-contract.yaml file.

    This is the single place in the codebase that turns untrusted YAML into
    a trusted, typed Contract. Every other component (engine, CLI, MCP)
    consumes the Contract object, never raw YAML.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No contract found at {path}. Run `infra-contract init` first.")

    raw = yaml.safe_load(path.read_text()) or {}
    try:
        return Contract.model_validate(raw)
    except ValidationError as exc:
        raise ContractLoadError(path, str(exc)) from exc


def default_contract_path(project_root: str | Path = ".") -> Path:
    return Path(project_root) / "infra-contract.yaml"


def contract_json_schema() -> dict:
    """Export JSON Schema so editors can autocomplete infra-contract.yaml."""
    return Contract.model_json_schema()
