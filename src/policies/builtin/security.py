from __future__ import annotations

from contracts.models import Contract, Severity
from engine.findings import Finding
from ir.model import Resource, ResourceKind
from policies.base import Policy


class NoPublicDatabasePolicy(Policy):
    id = "security.no-public-database"
    category = "security"
    default_severity = Severity.CRITICAL

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.DATABASE

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        allowed_public = contract.security.database.public_access
        is_public = resource.network.public
        violated = is_public and not allowed_public
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                "Database is publicly accessible."
                if violated
                else "Database is not publicly accessible."
            ),
            expected="public_access = false",
            actual=f"public_access = {is_public}",
            remediation=(
                "Set publicly_accessible = false and place the database in " "private subnets."
                if violated
                else None
            ),
        )


class NoPublicStoragePolicy(Policy):
    id = "security.no-public-storage"
    category = "security"
    default_severity = Severity.CRITICAL

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.STORAGE

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        allowed_public = contract.security.storage.public_access
        is_public = resource.network.public
        violated = is_public and not allowed_public
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                "Storage bucket is publicly accessible."
                if violated
                else "Storage bucket is not publicly accessible."
            ),
            expected="public_access = false",
            actual=f"public_access = {is_public}",
            remediation="Remove public ACL/policy grants from the bucket." if violated else None,
        )


class EncryptionRequiredPolicy(Policy):
    id = "security.encryption-required"
    category = "security"
    default_severity = Severity.HIGH

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind in (ResourceKind.DATABASE, ResourceKind.STORAGE, ResourceKind.CACHE)

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        requirement = (
            contract.security.database.encryption
            if resource.kind == ResourceKind.DATABASE
            else contract.security.storage.encryption
        )
        must_encrypt = requirement == "required"
        encrypted = resource.security.encrypted
        violated = must_encrypt and encrypted is False
        unknown = must_encrypt and encrypted is None
        return Finding(
            rule=self.id,
            severity=self.default_severity if violated else Severity.WARNING,
            resource_id=resource.id,
            category=self.category,
            passed=not violated and not unknown,
            message=(
                "Resource is not encrypted at rest."
                if violated
                else (
                    "Could not confirm encryption at rest."
                    if unknown
                    else "Resource is encrypted at rest."
                )
            ),
            expected="encryption = required",
            actual=f"encrypted = {encrypted}",
            remediation="Enable encryption at rest for this resource." if violated else None,
        )


class NoWildcardIamPolicy(Policy):
    id = "security.no-wildcard-iam"
    category = "security"
    default_severity = Severity.HIGH

    def applies_to(self, resource: Resource) -> bool:
        return resource.kind == ResourceKind.IAM

    def evaluate(self, resource: Resource, contract: Contract) -> Finding:
        forbidden = contract.security.iam.wildcard_permissions == "forbidden"
        has_wildcard = resource.security.wildcard_permissions
        violated = forbidden and has_wildcard
        return Finding(
            rule=self.id,
            severity=self.default_severity,
            resource_id=resource.id,
            category=self.category,
            passed=not violated,
            message=(
                "Wildcard IAM permissions detected."
                if violated
                else "No wildcard IAM permissions detected."
            ),
            expected="wildcard_permissions = forbidden",
            actual=f"wildcard = {has_wildcard}",
            remediation=(
                "Scope IAM Action/Resource to specific ARNs instead of '*'." if violated else None
            ),
        )


BUILTIN_SECURITY_POLICIES: list[Policy] = [
    NoPublicDatabasePolicy(),
    NoPublicStoragePolicy(),
    EncryptionRequiredPolicy(),
    NoWildcardIamPolicy(),
]
