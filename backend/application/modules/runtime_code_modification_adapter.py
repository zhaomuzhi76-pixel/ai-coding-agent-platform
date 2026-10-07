from __future__ import annotations

from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)


class RuntimeCodeModificationAdapter(
    CodeModificationProviderProtocol,
):
    """
    Application boundary adapter.

    Owns:
        - execution contract adaptation

    Does not own:
        - pipeline construction
        - proposal generation
        - runtime implementation
        - code modification logic
    """

    VERSION = "4.0"

    def __init__(
        self,
        provider: CodeModificationProviderProtocol,
    ) -> None:
        if not isinstance(
            provider,
            CodeModificationProviderProtocol,
        ):
            raise TypeError(
                "invalid code modification provider"
            )

        self.provider = provider

    async def execute(
        self,
        *,
        task: str,
        files: list[str],
        context: dict[str, object],
    ) -> object:
        return await self.provider.execute(
            task=task,
            files=files,
            context=context,
        )

    def ready(
        self,
    ) -> bool:
        return self.provider.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeCodeModificationAdapter",
]
