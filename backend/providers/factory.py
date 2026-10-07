from __future__ import annotations

from typing import Any

from backend.core.module.base_provider import BaseProvider


class ProviderFactory:
    """
    Provider constructor registry.

    Concrete provider types must inherit the canonical
    backend.core.module.BaseProvider.
    """

    VERSION = "3.0"

    def __init__(self) -> None:
        self._builders: dict[
            str,
            type[BaseProvider],
        ] = {}

    def register(
        self,
        provider_type: str,
        provider_class: type[BaseProvider],
    ) -> None:
        if not isinstance(provider_type, str):
            raise TypeError(
                "provider type must str"
            )

        normalized_type = provider_type.strip()
        if not normalized_type:
            raise ValueError(
                "provider type required"
            )

        if not isinstance(provider_class, type):
            raise TypeError(
                "provider class must type"
            )

        if not issubclass(
            provider_class,
            BaseProvider,
        ):
            raise TypeError(
                "provider class must extend "
                "core BaseProvider"
            )

        if normalized_type in self._builders:
            raise ValueError(
                f"provider already registered: "
                f"{normalized_type}"
            )

        self._builders[
            normalized_type
        ] = provider_class

    def create(
        self,
        provider_type: str,
        **kwargs: Any,
    ) -> BaseProvider:
        normalized_type = provider_type.strip()

        try:
            provider_class = self._builders[
                normalized_type
            ]
        except KeyError as exc:
            raise KeyError(
                f"unknown provider type: {normalized_type}"
            ) from exc

        return provider_class(**kwargs)

    def exists(self, provider_type: str) -> bool:
        return provider_type.strip() in self._builders

    def list_types(self) -> list[str]:
        return list(self._builders)

    def clear(self) -> None:
        self._builders.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "types": self.list_types(),
        }


__all__ = [
    "ProviderFactory",
]
