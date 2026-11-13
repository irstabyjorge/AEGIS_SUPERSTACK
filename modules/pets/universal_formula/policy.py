"""Default-deny policy gate for Universal Formula worker actions."""

from enum import Enum


class ActionClass(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    REPORT = "report"
    ADDITIVE_BRANCH_WRITE = "additive_branch_write"
    INSTALL = "install"
    DEPLOY = "deploy"
    PUBLISH = "publish"
    DELETE = "delete"
    PERMISSION_CHANGE = "permission_change"
    EXTERNAL_COMMUNICATION = "external_communication"


class PolicyGate:
    """Allows routine bounded work; consequential actions require explicit approval."""

    DEFAULT_ALLOWED = frozenset({
        ActionClass.READ,
        ActionClass.ANALYZE,
        ActionClass.REPORT,
        ActionClass.ADDITIVE_BRANCH_WRITE,
    })

    def __init__(self, approved_actions=()):
        self._approved = frozenset(approved_actions)

    def authorize(self, action):
        try:
            action = ActionClass(action)
        except ValueError:
            return False
        return action in self.DEFAULT_ALLOWED or action in self._approved
