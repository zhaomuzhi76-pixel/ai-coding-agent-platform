from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionDependencyBundle:
    """Runtime executor 只消费的不可变依赖包。"""

    llm_provider: object
    tools: object
    modification: object

    def ready(self) -> bool:
        return all((
            self.llm_provider is not None,
            self.tools is not None,
            self.modification is not None,
        ))

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "ready": self.ready(),
            "llm_provider": type(self.llm_provider).__name__,
            "tools": type(self.tools).__name__,
            "modification": type(self.modification).__name__,
        }


__all__ = ["ExecutionDependencyBundle"]
