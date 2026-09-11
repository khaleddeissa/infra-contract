from __future__ import annotations

from contracts.models import Contract

_TEMPLATE = """\
This repository uses infra-contract to govern infrastructure changes.

Contract file: `{contract_path}`

Before modifying infrastructure:

1. Read `{contract_path}` to understand what is allowed, forbidden, and required.
2. Follow the architecture constraints (approved compute: {compute}; approved database: {database}).
3. Keep production databases and storage private (`security.database.public_access = false`).
4. Run `infra-contract check` after making changes and fix any CRITICAL or HIGH findings.
5. Prefer `infra-contract plan` against a real Terraform plan before proposing infrastructure as final.
6. Do NOT apply changes directly to the production environment ({production_apply}).
7. Treat destructive changes (resource deletion/replacement of databases, storage, or caches) as
   requiring explicit human approval before merge.
8. Do not bypass, disable, or edit contract policies to make a failing check pass — fix the
   infrastructure or flag the conflict to a human instead.
9. If you are unsure whether a resource is approved, use the MCP tools
   (`infra_contract_get_architecture`, `infra_contract_check`) or ask a human, rather than guessing.

infra-contract is the source of truth for infrastructure rules in this repository, not this file's
memory of past conversations — always re-check the contract file, since it may change.
"""


def generate_agent_instructions(
    contract: Contract, contract_path: str = "infra-contract.yaml"
) -> str:
    return _TEMPLATE.format(
        contract_path=contract_path,
        compute=", ".join(contract.architecture.compute.allowed) or "(none declared)",
        database=", ".join(contract.architecture.database.allowed) or "(none declared)",
        production_apply="allowed" if contract.agent.production_apply else "forbidden",
    )
