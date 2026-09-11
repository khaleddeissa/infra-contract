"""
Normalized Infrastructure Model (the "IR")
===========================================

Policies never look at raw Terraform HCL, `terraform show -json`, a
Kubernetes manifest, or an AWS API response. They only ever look at this
normalized representation.

This is what makes multi-provider / multi-cloud support tractable: adding a
Kubernetes or Azure provider means writing a new `providers/*` adapter that
emits `Resource` objects — it never means touching the policy engine.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResourceKind(str, Enum):
    COMPUTE = "compute"
    DATABASE = "database"
    CACHE = "cache"
    STORAGE = "storage"
    NETWORK = "network"
    IAM = "iam"
    LOAD_BALANCER = "load_balancer"
    OTHER = "other"


class ChangeAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NO_OP = "no-op"
    REPLACE = "replace"


class NetworkProperties(BaseModel):
    public: bool = False
    subnet_type: str | None = None  # "public" | "private"
    ingress_cidrs: list[str] = Field(default_factory=list)


class SecurityProperties(BaseModel):
    encrypted: bool | None = None
    wildcard_permissions: bool = False


class ReliabilityProperties(BaseModel):
    backups_enabled: bool | None = None
    multi_az: bool | None = None
    deletion_protection: bool | None = None


class Resource(BaseModel):
    """A single normalized infrastructure resource."""

    id: str  # e.g. "aws_db_instance.production"
    kind: ResourceKind
    provider: str  # "aws", "azure", "gcp", "kubernetes"
    resource_type: str  # native type, e.g. "aws_db_instance"
    engine: str | None = None  # e.g. "postgres", "redis"
    region: str | None = None
    environment: str | None = None

    network: NetworkProperties = Field(default_factory=NetworkProperties)
    security: SecurityProperties = Field(default_factory=SecurityProperties)
    reliability: ReliabilityProperties = Field(default_factory=ReliabilityProperties)

    action: ChangeAction = ChangeAction.NO_OP  # populated when sourced from a plan
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)

    def is_production(self) -> bool:
        return (self.environment or "").lower() == "production"


class InfrastructureDocument(BaseModel):
    """The full normalized snapshot handed to the policy engine."""

    source: str  # "terraform-source" | "terraform-plan" | "kubernetes" | ...
    resources: list[Resource] = Field(default_factory=list)

    def by_kind(self, kind: ResourceKind) -> list[Resource]:
        return [r for r in self.resources if r.kind == kind]
