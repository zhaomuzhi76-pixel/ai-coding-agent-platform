from __future__ import annotations

from typing import Any

from backend.application.provider_gateway import (
    ApplicationProviderGatewayProtocol,
)


class CodeModificationProposalSupport:
    """Support owner for proposal validation and LLM schema."""

    VERSION = "1.0"

    @staticmethod
    def validate(
        task: str,
        file: str,
        source: str,
        provider: str,
        model: str,
    ) -> None:
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task required")
        if not isinstance(file, str) or not file.strip():
            raise ValueError("file required")
        if not isinstance(source, str):
            raise TypeError("source must str")
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider required")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model required")

    @staticmethod
    def response_format() -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "file": {"type": "string"},
                "operation": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
            },
            "required": (
                "file",
                "operation",
                "old",
                "new",
            ),
            "additionalProperties": False,
        }

    @staticmethod
    def require_provider(
        provider: ApplicationProviderGatewayProtocol,
    ) -> None:
        if not isinstance(
            provider,
            ApplicationProviderGatewayProtocol,
        ):
            raise TypeError(
                "provider gateway contract required"
            )

        if not provider.ready():
            raise RuntimeError(
                "provider gateway unavailable"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "CodeModificationProposalSupport",
]
