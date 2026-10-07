"""Model catalog + user-choice selector.

设计原则：模型由前端用户选择，后端不自动路由。
- ModelCatalog：给前端拉取可选模型清单（带能力/价格）
- ModelSelector：解析用户在请求里带的 model，返回唯一 provider+model
- FallbackChain（独立模块）：仅当用户选的主模型失败时，在
  同一 provider 内 fallback 到备用模型
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.providers.routing.capability_matrix import (
    CapabilityMatrix,
    ModelCapability,
)


@dataclass(frozen=True)
class ModelOption:
    """给前端展示的可选模型。"""
    model: str
    provider: str
    display_name: str
    context_window: int
    supports_tool_call: bool
    supports_stream: bool
    supports_embedding: bool
    cost_input_per_1k: float
    cost_output_per_1k: float
    strengths: tuple

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "provider": self.provider,
            "display_name": self.display_name,
            "context_window": self.context_window,
            "supports_tool_call": self.supports_tool_call,
            "supports_stream": self.supports_stream,
            "supports_embedding": self.supports_embedding,
            "cost_input_per_1k": self.cost_input_per_1k,
            "cost_output_per_1k": self.cost_output_per_1k,
            "strengths": list(self.strengths),
        }


@dataclass(frozen=True)
class Selection:
    """解析后的用户选择。"""
    model: str
    provider: str
    source: str  # "user" | "fallback_override" | "default"


class ModelCatalog:
    """前端可查询的模型清单。"""

    def __init__(self, matrix: CapabilityMatrix) -> None:
        self._matrix = matrix
        self._display: Dict[str, str] = {}

    def set_display_name(self, model: str, name: str) -> None:
        self._display[model] = name

    def list(self) -> List[ModelOption]:
        out: List[ModelOption] = []
        for name in self._matrix.names():
            cap = self._matrix.get(name)
            if cap is None:
                continue
            out.append(self._to_option(cap))
        return out

    def list_supporting(
        self,
        *,
        tool_call: bool = False,
        embedding: bool = False,
        stream: bool = False,
    ) -> List[ModelOption]:
        caps = self._matrix.find_supporting(
            tool_call=tool_call, embedding=embedding, stream=stream,
        )
        return [self._to_option(c) for c in caps]

    def get(self, model: str) -> Optional[ModelOption]:
        cap = self._matrix.get(model)
        return self._to_option(cap) if cap else None

    def _to_option(self, cap: ModelCapability) -> ModelOption:
        return ModelOption(
            model=cap.model,
            provider=cap.provider,
            display_name=self._display.get(cap.model, cap.model),
            context_window=cap.context_window,
            supports_tool_call=cap.supports_tool_call,
            supports_stream=cap.supports_stream,
            supports_embedding=cap.supports_embedding,
            cost_input_per_1k=cap.cost_input_per_1k,
            cost_output_per_1k=cap.cost_output_per_1k,
            strengths=tuple(cap.strengths),
        )

    def ready(self) -> bool:
        return self._matrix.ready()

    def dump(self) -> dict:
        return {
            "ready": self.ready(),
            "models": [o.model for o in self.list()],
        }


class ModelSelector:
    """把「用户请求里带的 model」解析成唯一 provider+model。

    后端不做自动路由。只做：
    1. 用户给了 model → 直接用
    2. 用户没给 model → 用 default（配置里写死的兜底）
    3. 用户给的 model 不在 catalog → 报错，让前端重选
    """

    def __init__(
        self,
        matrix: CapabilityMatrix,
        default_model: str = "",
    ) -> None:
        self._matrix = matrix
        self._default_model = default_model

    def select(self, user_choice: Optional[str]) -> Selection:
        if user_choice:
            cap = self._matrix.get(user_choice)
            if cap is None:
                raise ValueError(
                    f"model not in catalog: {user_choice} "
                    f"(frontend must re-select)"
                )
            return Selection(
                model=cap.model, provider=cap.provider, source="user",
            )
        if self._default_model:
            cap = self._matrix.get(self._default_model)
            if cap is not None:
                return Selection(
                    model=cap.model, provider=cap.provider, source="default",
                )
        raise ValueError(
            "no model selected and no default configured"
        )

    def require_embedding(self, selection: Selection) -> None:
        cap = self._matrix.get(selection.model)
        if cap is None or not cap.supports_embedding:
            raise ValueError(
                f"model {selection.model} does not support embedding"
            )

    def require_tool_call(self, selection: Selection) -> None:
        cap = self._matrix.get(selection.model)
        if cap is None or not cap.supports_tool_call:
            raise ValueError(
                f"model {selection.model} does not support tool_call"
            )

    def ready(self) -> bool:
        return self._matrix.ready()

    def dump(self) -> dict:
        return {
            "ready": self.ready(),
            "default_model": self._default_model,
        }


__all__ = ["ModelOption", "Selection", "ModelCatalog", "ModelSelector"]
