"""Built-in role presets."""
from __future__ import annotations

from typing import List

from backend.security.role import Role


def admin_role() -> Role:
    r = Role(name="admin", description="full access")
    r.grant_all([
        "*:manage", "*:read", "*:write", "*:execute", "*:delete",
    ])
    return r


def developer_role() -> Role:
    r = Role(name="developer", description="platform + tool + memory")
    r.grant_all([
        "platform:read", "platform:write", "platform:execute",
        "tool:read", "tool:execute",
        "memory:read", "memory:write",
        "mcp:read", "mcp:execute",
        "finetune:read", "finetune:execute",
    ])
    return r


def reviewer_role() -> Role:
    r = Role(name="reviewer", description="read + approve")
    r.grant_all([
        "platform:read", "tool:read", "memory:read",
    ])
    return r


def viewer_role() -> Role:
    r = Role(name="viewer", description="read only")
    r.grant_all([
        "platform:read", "memory:read", "tool:read",
    ])
    return r


def service_role() -> Role:
    r = Role(name="service", description="service account")
    r.grant_all([
        "platform:read", "platform:execute",
        "tool:execute", "memory:read", "memory:write",
        "mcp:execute",
    ])
    return r


def default_roles() -> List[Role]:
    return [
        admin_role(), developer_role(), reviewer_role(),
        viewer_role(), service_role(),
    ]


__all__ = [
    "admin_role", "developer_role", "reviewer_role",
    "viewer_role", "service_role", "default_roles",
]
