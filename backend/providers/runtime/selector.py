from __future__ import annotations

from backend.providers.registry import ProviderRegistry


class ProviderSelector:
    """
    Explicit provider selector.

    Provider selection is request-owned.
    Missing provider is a contract violation.
    No automatic provider fallback is allowed.
    """

    VERSION = "2.0"

    def __init__(
        self,
        registry: ProviderRegistry,
        default_provider: str,
    ) -> None:
        if registry is None:
            raise ValueError(
                "provider registry required"
            )
        if not isinstance(
            default_provider,
            str,
        ) or not default_provider.strip():
            raise ValueError(
                "configured provider required"
            )

        if not registry.exists(
            "llm",
            default_provider,
        ):
            raise LookupError(
                f"configured provider not found: "
                f"llm/{default_provider}"
            )

        self.registry = registry
        self.default_provider = default_provider.strip()

    def select(
        self,
        provider: str,
    ) -> str:
        if not isinstance(
            provider,
            str,
        ) or not provider.strip():
            raise ValueError(
                "explicit provider selection required"
            )

        selected = provider.strip()

        if not self.registry.exists(
            "llm",
            selected,
        ):
            raise LookupError(
                f"provider not found: llm/{selected}"
            )

        return selected

    def ready(self) -> bool:
        return bool(
            self.default_provider
            and self.registry.ready()
            and self.registry.exists(
                "llm",
                self.default_provider,
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "configured_provider": self.default_provider,
            "automatic_fallback": False,
            "ready": self.ready(),
        }


__all__ = [
    "ProviderSelector",
]
