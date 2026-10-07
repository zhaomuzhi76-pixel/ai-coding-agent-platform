"""SecurityBinding: HTTP adapter over static RBAC presets."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.security.presets import default_roles
from backend.security.principal import Principal
from backend.security.rbac import RBAC


class SecurityBinding:
    VERSION = "1.0"
    PREFIX = "/api/security"

    def __init__(self) -> None:
        self._rbac = RBAC()
        self._rbac.register_all(default_roles())

    def roles(self) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []
        for name in self._rbac.roles():
            role = self._rbac.role(name)
            if role is None:
                continue
            out.append(role.to_dict())
        return {"roles": out, "count": len(out)}

    def role(self, name: str) -> Dict[str, Any]:
        role = self._rbac.role(name)
        if role is None:
            raise KeyError(f"role not found: {name}")
        return role.to_dict()

    def check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(payload.get("user_id", "")).strip()
        tenant_id = str(payload.get("tenant_id", "")).strip()
        roles = tuple(payload.get("roles", []) or [])
        permission = str(payload.get("permission", "")).strip()
        if not user_id or not tenant_id:
            raise ValueError("user_id and tenant_id required")
        if not permission:
            raise ValueError("permission required")
        principal = Principal(
            user_id=user_id, tenant_id=tenant_id, roles=roles,
        )
        return self._rbac.evaluate(principal, permission).to_dict()

    def summary(self) -> Dict[str, Any]:
        roles = self._rbac.roles()
        total_perms = sum(
            len((self._rbac.role(r) or type("X", (), {"permissions": set()})()).permissions)
            for r in roles
        )
        return {
            "roles": len(roles),
            "permissions": total_perms,
            "tenants": 0,
            "audit_entries": 0,
            "denials": 0,
            "note": "tenant/audit 运行期数据待接入",
        }

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "prefix": self.PREFIX,
            "ready": self.ready(),
        }


__all__ = ["SecurityBinding"]
