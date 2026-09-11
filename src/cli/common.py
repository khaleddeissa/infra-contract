from __future__ import annotations

from pathlib import Path

from contracts.loader import default_contract_path, load_contract
from contracts.models import Contract
from ir.model import InfrastructureDocument
from providers.terraform.provider import TerraformProvider


def load_contract_or_exit(contract_path: str | None, project_root: str = ".") -> Contract:
    path = Path(contract_path) if contract_path else default_contract_path(project_root)
    return load_contract(path)


def build_document(
    project_root: str = ".",
    plan_path: str | None = None,
    target: str | None = None,
) -> InfrastructureDocument:
    """Resolve the normalized infrastructure document to evaluate.

    Priority: an explicit `terraform show -json` plan (highest confidence)
    over a best-effort scan of raw .tf source (lower confidence).
    """
    provider = TerraformProvider()

    if plan_path:
        return provider.load(Path(plan_path))

    root = Path(target) if target else Path(project_root)
    return provider.from_source_dir(root)
