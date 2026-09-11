from __future__ import annotations

from infra_contract.policies.base import Policy
from infra_contract.policies.builtin.architecture import BUILTIN_ARCHITECTURE_POLICIES
from infra_contract.policies.builtin.networking import BUILTIN_NETWORKING_POLICIES
from infra_contract.policies.builtin.reliability import BUILTIN_RELIABILITY_POLICIES
from infra_contract.policies.builtin.security import BUILTIN_SECURITY_POLICIES

ALL_BUILTIN_POLICIES: list[Policy] = [
    *BUILTIN_SECURITY_POLICIES,
    *BUILTIN_NETWORKING_POLICIES,
    *BUILTIN_RELIABILITY_POLICIES,
    *BUILTIN_ARCHITECTURE_POLICIES,
]

POLICY_BY_ID: dict[str, Policy] = {p.id: p for p in ALL_BUILTIN_POLICIES}

__all__ = ["ALL_BUILTIN_POLICIES", "POLICY_BY_ID"]
