"""Tenant: organization boundary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Tenant:
    tenant_id: str
    name: str
    plan: str = "standard"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id required")
        if not self.name.strip():
            raise ValueError("tenant name required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "plan": self.plan,
            "metadata": dict(self.metadata),
        }

    def dump(self) -> Dict[str, Any]:
        return self.to_dict()


__all__ = ["Tenant"]
