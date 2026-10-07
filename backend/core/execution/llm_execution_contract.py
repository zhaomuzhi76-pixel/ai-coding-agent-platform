from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMExecutionProviderProtocol(Protocol):
    """
    Core contract for provider-backed LLM execution.

    This contract belongs to the execution core because both
    Application adapters and Runtime implementations consume it.
    """

    async def chat(
        self,
        *,
        provider: str,
        model: str,
        messages: list[dict[str, str]],
    ) -> object:
        ...

    def ready(
        self,
    ) -> bool:
        ...


__all__ = [
    "LLMExecutionProviderProtocol",
]
