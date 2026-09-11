from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "infra_contract"

# Modules that must stay provider- and interface-agnostic.
CORE_PACKAGES = ["contracts", "engine", "policies", "ir"]

# These are the only outward-facing layers allowed to import providers/cli/mcp.
FORBIDDEN_IMPORT_PREFIXES = (
    "infra_contract.providers",
    "infra_contract.cli",
    "infra_contract.mcp",
)


def _imported_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_core_packages_do_not_import_providers_cli_or_mcp():
    violations = []
    for package in CORE_PACKAGES:
        for py_file in (SRC / package).rglob("*.py"):
            for module in _imported_modules(py_file):
                if module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{py_file.relative_to(SRC)} imports {module}")

    assert not violations, (
        "Dependency direction violated — contracts/engine/policies/ir must never "
        "import providers, cli, or mcp:\n" + "\n".join(violations)
    )


def test_ir_does_not_import_contracts_or_engine():
    """The normalized IR must stay a pure data model with no knowledge of
    the contract schema or evaluation logic — that keeps it reusable by any
    future provider without pulling in policy code."""
    violations = []
    for py_file in (SRC / "ir").rglob("*.py"):
        for module in _imported_modules(py_file):
            if module.startswith(("infra_contract.contracts", "infra_contract.engine")):
                violations.append(f"{py_file.relative_to(SRC)} imports {module}")
    assert not violations, "\n".join(violations)
