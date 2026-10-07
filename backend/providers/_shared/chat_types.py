"""Unified LLM chat types — 跨 provider 统一语义层。

调用方只用统一字段：
    format="json"    → 各 provider 自翻译
    thinking=True    → 各 provider 自翻译
    temperature/max_tokens/top_p/stop/tools → 通用
    extra            → 厂商特有透传（不推荐）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UnifiedParams:
    model: str = ""
    format: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[List[str]] = None
    thinking: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_kwargs(cls, kwargs: Dict[str, Any]) -> "UnifiedParams":
        k = dict(kwargs or {})
        return cls(
            model=str(k.pop("model", "") or ""),
            format=k.pop("format", None),
            temperature=float(k.pop("temperature", 0.7)),
            max_tokens=k.pop("max_tokens", None),
            top_p=k.pop("top_p", None),
            stop=k.pop("stop", None),
            thinking=bool(k.pop("thinking", False)),
            tools=k.pop("tools", None),
            extra=k,
        )


@dataclass
class ChatResponse:
    content: str = ""
    reasoning: str = ""
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "reasoning": self.reasoning,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "finish_reason": self.finish_reason,
        }


__all__ = ["UnifiedParams", "ChatResponse"]
