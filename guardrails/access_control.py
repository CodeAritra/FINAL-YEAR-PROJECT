"""
Access Control and Authorization Guardrail.
Enforces Role-Based Access Control (RBAC) and classification clearance levels.
Keeps authorization decisions cleanly separated from safety classification.
"""

from enum import Enum
from pydantic import BaseModel


class DataSensitivity(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class UserRole(str, Enum):
    ANONYMOUS = "ANONYMOUS"
    RESEARCHER = "RESEARCHER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class AuthorizationResult(BaseModel):
    is_authorized: bool
    user_role: UserRole
    required_clearance: DataSensitivity
    reason: str


class AccessControlEngine:
    """Evaluates whether a user's role grants clearance to access specific data sensitivity tiers."""

    ROLE_CLEARANCE_HIERARCHY: dict[UserRole, list[DataSensitivity]] = {
        UserRole.ANONYMOUS: [DataSensitivity.PUBLIC],
        UserRole.RESEARCHER: [DataSensitivity.PUBLIC, DataSensitivity.INTERNAL],
        UserRole.STAFF: [DataSensitivity.PUBLIC, DataSensitivity.INTERNAL, DataSensitivity.CONFIDENTIAL],
        UserRole.ADMIN: [
            DataSensitivity.PUBLIC,
            DataSensitivity.INTERNAL,
            DataSensitivity.CONFIDENTIAL,
            DataSensitivity.RESTRICTED,
        ],
    }

    def check_access(
        self,
        user_role: UserRole | str,
        resource_sensitivity: DataSensitivity | str,
    ) -> AuthorizationResult:
        """Verify if user has permission to access the resource."""
        if isinstance(user_role, str):
            user_role = UserRole(user_role.upper())
        if isinstance(resource_sensitivity, str):
            resource_sensitivity = DataSensitivity(resource_sensitivity.upper())

        allowed_tiers = self.ROLE_CLEARANCE_HIERARCHY.get(user_role, [DataSensitivity.PUBLIC])

        if resource_sensitivity in allowed_tiers:
            return AuthorizationResult(
                is_authorized=True,
                user_role=user_role,
                required_clearance=resource_sensitivity,
                reason=f"Role '{user_role.value}' is authorized for '{resource_sensitivity.value}' data.",
            )

        return AuthorizationResult(
            is_authorized=False,
            user_role=user_role,
            required_clearance=resource_sensitivity,
            reason=f"Access Denied: Role '{user_role.value}' lacks required clearance '{resource_sensitivity.value}'.",
        )

