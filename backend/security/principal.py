"""Principal: authenticated user/agent context."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    roles: tuple = ()
    is_service: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.user_id.strip():
            raise ValueError("user_id required")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id required")

    def with_role(self, role: str) -> "Principal":
        roles = tuple(sorted(set(self.roles) | {role}))
        return Principal(
            user_id=self.user_id, tenant_id=self.tenant_id,
            roles=roles, is_service=self.is_service,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "roles": list(self.roles),
            "is_service": self.is_service,
            "metadata": dict(self.metadata),
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


__all__ = ["Principal"]
