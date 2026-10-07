"""Role: named set of permissions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from backend.security.permission import Permission


@dataclass
class Role:
    name: str
    permissions: Set[str] = field(default_factory=set)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("role name required")

    def grant(self, permission: str) -> None:
        Permission.parse(permission)
        self.permissions.add(permission.strip())

    def grant_all(self, permissions: List[str]) -> None:
        for p in permissions:
            self.grant(p)

    def revoke(self, permission: str) -> None:
        self.permissions.discard(permission.strip())

    def has(self, permission: str) -> bool:
        try:
            target = Permission.parse(permission)
        except ValueError:
            return False
        for raw in self.permissions:
            try:
                granted = Permission.parse(raw)
            except ValueError:
                continue
            if granted.matches(target):
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "permissions": sorted(self.permissions),
            "description": self.description,
        }

    def dump(self) -> dict:
        return self.to_dict()


__all__ = ["Role"]
