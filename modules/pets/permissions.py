"""Small deny-by-default RBAC policy for PETS.

The authenticated server must derive the role from a trusted identity provider.
Never accept a role supplied by an untrusted request body.
"""
from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    READER = "reader"


class Permission(str, Enum):
    READ_STATUS = "read:status"
    READ_EVIDENCE = "read:evidence"
    CREATE_EVIDENCE = "create:evidence"
    VERIFY_EVIDENCE = "verify:evidence"
    MANAGE_USERS = "manage:users"
    MANAGE_INTEGRATIONS = "manage:integrations"
    DEPLOY = "deploy"


_ROLE_PERMISSIONS = {
    Role.OWNER: frozenset(Permission),
    Role.ADMIN: frozenset({
        Permission.READ_STATUS, Permission.READ_EVIDENCE,
        Permission.CREATE_EVIDENCE, Permission.VERIFY_EVIDENCE,
        Permission.MANAGE_USERS, Permission.MANAGE_INTEGRATIONS,
    }),
    Role.ANALYST: frozenset({
        Permission.READ_STATUS, Permission.READ_EVIDENCE,
        Permission.CREATE_EVIDENCE, Permission.VERIFY_EVIDENCE,
    }),
    Role.AUDITOR: frozenset({
        Permission.READ_STATUS, Permission.READ_EVIDENCE,
        Permission.VERIFY_EVIDENCE,
    }),
    Role.READER: frozenset({Permission.READ_STATUS}),
}


def authorize(role: Role | str, permission: Permission | str) -> bool:
    """Return False for unknown roles/permissions; never grant by default."""
    try:
        normalized_role = Role(role)
        normalized_permission = Permission(permission)
    except (TypeError, ValueError):
        return False
    return normalized_permission in _ROLE_PERMISSIONS[normalized_role]


def require_permission(role: Role | str, permission: Permission | str) -> None:
    if not authorize(role, permission):
        raise PermissionError("permission_denied")
