from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class EditContext:
    task: str
    file: str
    source: str
    plan: str = ""
    prior_feedback: str = ""
    attempt: int = 0
    max_attempts: int = 3
    # ★ 多文件：{相对路径: 内容}，供 coder 理解整个调用链
    related_files: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoleResult:
    role: str
    ok: bool
    data: dict[str, Any]
    error: str | None = None


@runtime_checkable
class AgentRoleProtocol(Protocol):
    name: str
    version: str

    async def run(
        self,
        *,
        context: EditContext,
        gateway: Any,
        router: Any,
    ) -> RoleResult:
        ...

    def ready(self) -> bool:
        ...

    def dump(self) -> dict[str, Any]:
        ...


__all__ = ["EditContext", "RoleResult", "AgentRoleProtocol"]
