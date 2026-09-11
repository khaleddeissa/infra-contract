from __future__ import annotations

import pytest

from infra_contract.contracts.loader import ContractLoadError, load_contract


def test_load_valid_contract(tmp_path):
    contract_yaml = tmp_path / "infra-contract.yaml"
    contract_yaml.write_text(
        """
version: "1"
project:
  name: demo
security:
  database:
    public_access: false
"""
    )
    contract = load_contract(contract_yaml)
    assert contract.project.name == "demo"
    assert contract.security.database.public_access is False


def test_load_missing_contract_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_contract(tmp_path / "does-not-exist.yaml")


def test_load_invalid_contract_raises(tmp_path):
    contract_yaml = tmp_path / "infra-contract.yaml"
    contract_yaml.write_text("project:\n  name: demo\nunknown_top_level_key: true\n")
    with pytest.raises(ContractLoadError):
        load_contract(contract_yaml)
