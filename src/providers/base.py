from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ir.model import InfrastructureDocument


class InfrastructureProvider(ABC):
    """Common interface for every infrastructure source (Terraform, AWS,
    Kubernetes, ...). A provider's only job is: raw source -> Resource IR.

    It must never know about policies or the Contract schema. That keeps the
    dependency arrow pointing one way: providers -> ir, never providers ->
    engine.
    """

    name: str

    @abstractmethod
    def discover(self, path: Path) -> bool:
        """Return True if this provider recognizes content at `path`."""

    @abstractmethod
    def parse(self, path: Path) -> dict:
        """Parse raw source into a provider-native intermediate dict."""

    @abstractmethod
    def normalize(self, parsed: dict) -> InfrastructureDocument:
        """Convert provider-native data into the normalized IR."""

    def load(self, path: Path) -> InfrastructureDocument:
        parsed = self.parse(path)
        return self.normalize(parsed)
