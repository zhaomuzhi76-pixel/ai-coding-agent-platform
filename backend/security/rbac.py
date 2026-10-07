"""RBAC evaluator: principal + roles → allowed/denied."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.security.principal import Principal
from backend.security.role import Role


@dataclass
class Decision:
    allowed: bool
    reason: str
    matched_role: str = ""
    permission: str = ""

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "matched_role": self.matched_role,
            "permission": self.permission,
        }


class RBAC:
    VERSION = "1.0"

    def __init__(self) -> None:
        self._roles: Dict[str, Role] = {}

    def register(self, role: Role) -> None:
        self._roles[role.name] = role

    def register_all(self, roles: List[Role]) -> None:
        for r in roles:
            self.register(r)

    def role(self, name: str) -> Optional[Role]:
        return self._roles.get(name)

    def roles(self) -> List[str]:
        return sorted(self._roles.keys())

    def evaluate(self, principal: Principal, permission: str) -> Decision:
        if not principal.roles:
            return Decision(
                allowed=False, reason="no_roles_assigned",
                permission=permission,
            )
        for role_name in principal.roles:
            role = self._roles.get(role_name)
            if role is None:
                continue
            if role.has(permission):
                return Decision(
                    allowed=True,
                    reason=f"granted_by:{role_name}",
                    matched_role=role_name,
                    permission=permission,
                )
        return Decision(
            allowed=False, reason="no_role_grants_permission",
            permission=permission,
        )

    def require(self, principal: Principal, permission: str) -> None:
        d = self.evaluate(principal, permission)
        if not d.allowed:
            raise PermissionError(
                f"{permission} denied for user={principal.user_id} "
                f"tenant={principal.tenant_id} reason={d.reason}"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "roles": self.roles(),
        }


__all__ = ["Decision", "RBAC"]
