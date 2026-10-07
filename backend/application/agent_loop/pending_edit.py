"""PendingEdit: 一次挂起等待审批的写操作。

工业级契约：
    - 每个写操作生成唯一 edit_id
    - 携带 diff（供前端展示）
    - 不可变数据类，构造即合法
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


def _new_id() -> str:
    return "pe-" + uuid.uuid4().hex[:12]


@dataclass(frozen=True, slots=True)
class PendingEdit:
    edit_id: str
    action: str
    path: str
    old_content: str | None
    new_content: str | None
    diff: str
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(
        cls,
        action: str,
        path: str,
        old_content: str | None,
        new_content: str | None,
        diff: str,
    ) -> "PendingEdit":
        return cls(
            edit_id=_new_id(),
            action=action,
            path=path,
            old_content=old_content,
            new_content=new_content,
            diff=diff,
        )

    def to_wire(self) -> dict:
        return {
            "edit_id": self.edit_id,
            "action": self.action,
            "path": self.path,
            "diff": self.diff,
            "created_at": self.created_at,
            "has_old": self.old_content is not None,
            "has_new": self.new_content is not None,
        }


__all__ = ["PendingEdit"]
