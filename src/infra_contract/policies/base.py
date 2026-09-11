from __future__ import annotations

from abc import ABC, abstractmethod

from infra_contract.contracts.models import Contract, Severity
from infra_contract.engine.findings import Finding
from infra_contract.ir.model import InfrastructureDocument, Resource


class Policy(ABC):
    """A single, composable rule.

    A Policy only ever depends on `contracts` and `ir` — never on a specific
    provider. This is what lets the same `no-public-database` policy apply
    whether the database came from Terraform, a future Kubernetes operator,
    or a live AWS API scan.
    """

    id: str
    category: str
    default_severity: Severity = Severity.HIGH

    @abstractmethod
    def applies_to(self, resource: Resource) -> bool:
        """Whether this policy has an opinion about `resource`."""

    @abstractmethod
    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        """Evaluate one resource this policy applies to."""

    def run(self, document: InfrastructureDocument, contract: Contract) -> list[Finding]:
        return [
            self.evaluate(resource, contract)
            for resource in document.resources
            if self.applies_to(resource)
        ]
