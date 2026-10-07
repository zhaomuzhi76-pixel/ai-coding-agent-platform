"""Model capability matrix: which model can do what."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ModelCapability:
    model: str
    provider: str
    context_window: int
    max_output: int
    supports_tool_call: bool = False
    supports_stream: bool = True
    supports_embedding: bool = False
    cost_input_per_1k: float = 0.0
    cost_output_per_1k: float = 0.0
    strengths: tuple = ()


class CapabilityMatrix:
    """Registry of model capabilities, keyed by model id."""

    def __init__(self) -> None:
        self._models: Dict[str, ModelCapability] = {}

    def register(self, cap: ModelCapability) -> None:
        self._models[cap.model] = cap

    def register_all(self, caps: List[ModelCapability]) -> None:
        for c in caps:
            self.register(c)

    def get(self, model: str) -> Optional[ModelCapability]:
        return self._models.get(model)

    def names(self) -> List[str]:
        return sorted(self._models.keys())

    def find_by_strength(
        self, strength: str, min_context: int = 0,
    ) -> List[ModelCapability]:
        return [
            c for c in self._models.values()
            if strength in c.strengths
            and c.context_window >= min_context
        ]

    def find_supporting(
        self,
        *,
        tool_call: bool = False,
        embedding: bool = False,
        stream: bool = False,
        min_context: int = 0,
    ) -> List[ModelCapability]:
        out: List[ModelCapability] = []
        for c in self._models.values():
            if tool_call and not c.supports_tool_call:
                continue
            if embedding and not c.supports_embedding:
                continue
            if stream and not c.supports_stream:
                continue
            if c.context_window < min_context:
                continue
            out.append(c)
        return out

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {
            "ready": self.ready(),
            "models": len(self._models),
            "names": self.names(),
        }
