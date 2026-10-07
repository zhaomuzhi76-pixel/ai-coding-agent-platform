"""L1 配置中心 Reranker 卡片契约 —— 前端展示格式（纯数据）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STATUS_LABEL: dict[str, str] = {
    "untested": "未测试",
    "probing":  "测试中",
    "passing":  "通过",
    "failing":  "未通过",
    "disabled": "已禁用",
}

STATUS_COLOR: dict[str, str] = {
    "untested": "gray",
    "probing":  "blue",
    "passing":  "green",
    "failing":  "red",
    "disabled": "gray",
}


@dataclass(frozen=True)
class RerankerModelEntry:
    model_id: str
    display_name: str
    backend_kind: str
    endpoint: str
    description: str
    weight: float
    tags: tuple[str, ...]

    def to_card_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "backend_kind": self.backend_kind,
            "endpoint": self.endpoint,
            "description": self.description,
            "weight": self.weight,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class RerankerCardEntry:
    entry: RerankerModelEntry
    status: str
    selectable: bool
    selected: bool
    status_label: str
    status_color: str
    last_probe_at: str
    last_outcome: str
    last_message: str
    last_latency_ms: float
    actions: tuple[str, ...] = ("probe", "select")

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.entry.to_card_dict(),
            "status": self.status,
            "status_label": self.status_label,
            "status_color": self.status_color,
            "selectable": self.selectable,
            "selected": self.selected,
            "last_probe_at": self.last_probe_at,
            "last_outcome": self.last_outcome,
            "last_message": self.last_message,
            "last_latency_ms": self.last_latency_ms,
            "actions": list(self.actions),
        }


def label_of(status: str) -> str:
    return STATUS_LABEL.get(status, status)


def color_of(status: str) -> str:
    return STATUS_COLOR.get(status, "gray")
