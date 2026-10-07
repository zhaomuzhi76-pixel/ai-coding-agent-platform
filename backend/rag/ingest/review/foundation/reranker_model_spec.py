"""L1 排序模型规格 —— 前端下拉列表的数据源。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RerankerModelSpec:
    model_id: str
    display_name: str
    backend_kind: str = "builtin"
    endpoint: str = ""
    model_path: str = ""
    weight: float = 1.0
    description: str = ""
    tags: tuple[str, ...] = ()
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "backend_kind": self.backend_kind,
            "endpoint": self.endpoint,
            "model_path": self.model_path,
            "weight": self.weight,
            "description": self.description,
            "tags": list(self.tags),
            "options": dict(self.options),
        }


DEFAULT_SPEC_ID = "builtin-qwen3-reranker"


def build_default_spec() -> RerankerModelSpec:
    return RerankerModelSpec(
        model_id=DEFAULT_SPEC_ID,
        display_name="Qwen3-Reranker-4B（内置）",
        backend_kind="builtin",
        description="通过 backend.rag.reranker_server 加载的默认重排模型",
        tags=("default", "gguf"),
    )
