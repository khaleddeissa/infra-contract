from __future__ import annotations

from pydantic import BaseModel

from contracts.models import Severity


class Finding(BaseModel):
    """A single, concrete contract violation (or pass) for one resource."""

    rule: str
    severity: Severity
    resource_id: str
    category: str  # "security" | "networking" | "reliability" | "architecture" | ...
    message: str
    expected: str | None = None
    actual: str | None = None
    remediation: str | None = None
    passed: bool = False

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
