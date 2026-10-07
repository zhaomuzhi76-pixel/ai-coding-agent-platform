"""Item: 一次工具调用 / 审批 / 步骤（Codex 三级模型第三级）。"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


KINDS = frozenset({
    "step",            # 一步工具调用
    "result",          # turn 最终结果
    "pending_edit",    # 请求审批
    "decision",        # 用户批准 / 拒绝
})


@dataclass(frozen=True, slots=True)
class Item:
    item_id: str
    turn_id: str
    kind: str
    data: dict = field(default_factory=dict)
    created_at: float = 0.0

    @classmethod
    def create(
        cls, turn_id: str, kind: str, data: dict,
    ) -> "Item":
        if kind not in KINDS:
            raise ValueError(f"unknown kind: {kind}")
        return cls(
            item_id="it-" + uuid.uuid4().hex[:12],
            turn_id=turn_id,
            kind=kind,
            data=dict(data),
            created_at=time.time(),
        )

    def to_mongo(self) -> dict:
        return {
            "item_id": self.item_id,
            "turn_id": self.turn_id,
            "kind": self.kind,
            "data": self.data,
            "created_at": self.created_at,
        }

    @classmethod
    def from_mongo(cls, doc: dict) -> "Item":
        return cls(
            item_id=str(doc["item_id"]),
            turn_id=str(doc["turn_id"]),
            kind=str(doc.get("kind", "step")),
            data=dict(doc.get("data", {})),
            created_at=float(doc.get("created_at", 0)),
        )


__all__ = ["Item", "KINDS"]
