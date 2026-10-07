"""工具规格：定义 LLM 可调用的工具。"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        if not self.parameters:
            return f"- {self.name}(): {self.description}"
        args = ", ".join(f"{k}: {v}" for k, v in self.parameters.items())
        return f"- {self.name}({args}): {self.description}"


__all__ = ["ToolSpec"]
