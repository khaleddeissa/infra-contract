"""
Contract Models
===============

This module defines the *only* thing every other layer of infra-contract is
allowed to depend on upward: the declarative Contract schema.

Dependency rule enforced by this codebase:

    contracts (this file)
        ^
        |
    engine / policies   (read contracts, know nothing about Terraform/AWS/K8s)
        ^
        |
    ir                  (normalized representation, provider-agnostic)
        ^
        |
    providers/terraform, providers/aws, providers/kubernetes
        ^
        |
    cli, mcp, integrations/github (thin consumers of the engine)

Nothing in `contracts/` or `engine/` may import from `providers/`, `cli/`,
or `mcp/`. That import direction is checked in tests/test_architecture.py.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class EnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = "production"


class CloudConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    provider: str = "aws"
    regions_allowed: list[str] = Field(default_factory=list, alias="regions")

    @property
    def allowed_regions(self) -> list[str]:
        return self.regions_allowed


class ComponentAllowList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)


class ArchitectureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    compute: ComponentAllowList = Field(default_factory=ComponentAllowList)
    database: ComponentAllowList = Field(default_factory=ComponentAllowList)
    cache: ComponentAllowList = Field(default_factory=ComponentAllowList)
    storage: ComponentAllowList = Field(default_factory=ComponentAllowList)


class DatabaseSecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_access: bool = False
    encryption: str = "required"  # "required" | "optional" | "forbidden"


class StorageSecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_access: bool = False
    encryption: str = "required"


class IamSecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    wildcard_permissions: str = "forbidden"  # "forbidden" | "allowed"


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database: DatabaseSecurityConfig = Field(default_factory=DatabaseSecurityConfig)
    storage: StorageSecurityConfig = Field(default_factory=StorageSecurityConfig)
    iam: IamSecurityConfig = Field(default_factory=IamSecurityConfig)


class NetworkingDatabaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    public_subnet: str = "forbidden"  # "forbidden" | "allowed"
    private_subnet_required: bool = True


class NetworkingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database: NetworkingDatabaseConfig = Field(default_factory=NetworkingDatabaseConfig)


class ReliabilityProductionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    backups: str = "required"  # "required" | "optional"
    multi_az: str = "required"  # "required" | "optional"
    deletion_protection: str = "optional"


class ReliabilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    production: ReliabilityProductionConfig = Field(default_factory=ReliabilityProductionConfig)


class ObservabilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    logs: bool = True
    metrics: bool = True
    tracing: bool = True


class CostConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monthly_budget_usd: float | None = None
    max_increase_percent: float | None = None


class DestructiveChangesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    require_human_approval: bool = True


class AgentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    production_apply: bool = Field(default=False, description="May an agent apply to production?")
    destructive_changes: DestructiveChangesConfig = Field(
        default_factory=DestructiveChangesConfig
    )


class PoliciesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: list[str] = Field(default_factory=list)
    disabled: list[str] = Field(default_factory=list)


class CiConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fail_on: list[Severity] = Field(
        default_factory=lambda: [Severity.CRITICAL, Severity.HIGH]
    )


class Contract(BaseModel):
    """The root, version-controlled infrastructure contract."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1"
    project: ProjectConfig
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    cloud: CloudConfig = Field(default_factory=CloudConfig)
    architecture: ArchitectureConfig = Field(default_factory=ArchitectureConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    networking: NetworkingConfig = Field(default_factory=NetworkingConfig)
    reliability: ReliabilityConfig = Field(default_factory=ReliabilityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    policies: PoliciesConfig = Field(default_factory=PoliciesConfig)
    ci: CiConfig = Field(default_factory=CiConfig)

    def is_policy_enabled(self, policy_id: str) -> bool:
        if policy_id in self.policies.disabled:
            return False
        if self.policies.enabled:
            return policy_id in self.policies.enabled
        return True
