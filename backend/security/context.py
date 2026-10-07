"""SecurityContext: bind principal + rbac + audit + tenant."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.security.audit import AuditLog
from backend.security.principal import Principal
from backend.security.rbac import Decision, RBAC
from backend.security.tenant import Tenant


class SecurityContext:
    VERSION = "1.0"

    def __init__(
        self,
        *,
        rbac: RBAC,
        audit: Optional[AuditLog] = None,
        tenants: Optional[Dict[str, Tenant]] = None,
    ) -> None:
        self._rbac = rbac
        self._audit = audit or AuditLog()
        self._tenants = dict(tenants or {})

    @property
    def rbac(self) -> RBAC:
        return self._rbac

    @property
    def audit(self) -> AuditLog:
        return self._audit

    def register_tenant(self, tenant: Tenant) -> None:
        self._tenants[tenant.tenant_id] = tenant

    def tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def tenants(self) -> list:
        return sorted(self._tenants.keys())

    def check(
        self,
        principal: Principal,
        permission: str,
        *,
        action: str = "",
        resource: str = "",
    ) -> Decision:
        d = self._rbac.evaluate(principal, permission)
        self._audit.record(
            principal_user=principal.user_id,
            principal_tenant=principal.tenant_id,
            action=action or permission,
            resource=resource or permission,
            allowed=d.allowed,
            reason=d.reason,
        )
        return d

    def require(
        self,
        principal: Principal,
        permission: str,
        *,
        action: str = "",
        resource: str = "",
    ) -> None:
        d = self.check(
            principal, permission, action=action, resource=resource,
        )
        if not d.allowed:
            raise PermissionError(
                f"{permission} denied (user={principal.user_id}, "
                f"tenant={principal.tenant_id}, reason={d.reason})"
            )

    def ready(self) -> bool:
        return self._rbac.ready() and self._audit.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "roles": self._rbac.roles(),
            "tenants": self.tenants(),
            "audit_count": self._audit.count(),
        }


__all__ = ["SecurityContext"]
