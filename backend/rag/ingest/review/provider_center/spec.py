"""provider_center 规格定义 —— 通用 Provider 模型 spec。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# 复用 L1 已有的状态枚举（避免职责重复）
from backend.rag.ingest.review.foundation.reranker_model_status import (
    ModelStatus,
    ProbeOutcome,
)

KIND_LLM = "llm"
KIND_EMBEDDING = "embedding"
KIND_RERANKER = "reranker"
SUPPORTED_KINDS = (KIND_LLM, KIND_EMBEDDING, KIND_RERANKER)


@dataclass(frozen=True)
class ProviderSpec:
    kind: str
    model_id: str
    display_name: str
    backend_kind: str = "openai_compatible"
    endpoint: str = ""
    api_key_env: str = ""
    model_path: str = ""
    weight: float = 1.0
    description: str = ""
    tags: tuple[str, ...] = ()
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "model_id": self.model_id,
            "display_name": self.display_name,
            "backend_kind": self.backend_kind,
            "endpoint": self.endpoint,
            "api_key_env": self.api_key_env,
            "model_path": self.model_path,
            "weight": self.weight,
            "description": self.description,
            "tags": list(self.tags),
            "options": dict(self.options),
        }


__all__ = [
    "KIND_LLM", "KIND_EMBEDDING", "KIND_RERANKER", "SUPPORTED_KINDS",
    "ProviderSpec", "ModelStatus", "ProbeOutcome",
]
