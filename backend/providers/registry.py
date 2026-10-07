from __future__ import annotations

from backend.providers.contracts import ProviderProtocol


class ProviderRegistry:
    """
    Provider registration boundary.

    Stores provider definitions by category and name.
    """

    VERSION = "1.0"

    def __init__(self) -> None:
        self._providers: dict[
            str,
            dict[str, ProviderProtocol],
        ] = {}

    def register(
        self,
        provider: ProviderProtocol,
    ) -> None:
        if provider is None:
            raise ValueError("provider required")
        if not isinstance(
            provider,
            ProviderProtocol,
        ):
            raise TypeError("invalid provider")
        category = provider.category
        name = provider.name
        if not category:
            raise ValueError("provider category required")
        if not name:
            raise ValueError("provider name required")
        bucket = self._providers.setdefault(
            category,
            {},
        )
        if name in bucket:
            raise ValueError(
                f"provider already registered: {category}/{name}"
            )
        bucket[name] = provider

    def resolve(
        self,
        category: str,
        name: str,
    ) -> ProviderProtocol:
        try:
            return self._providers[
                category
            ][name]
        except KeyError as error:
            raise LookupError(
                f"provider not found: {category}/{name}"
            ) from error

    def exists(
        self,
        category: str,
        name: str,
    ) -> bool:
        return (
            category in self._providers
            and name in self._providers[category]
        )

    def names(
        self,
        category: str | None = None,
    ) -> tuple[str, ...]:
        if category is not None:
            return tuple(
                self._providers.get(
                    category,
                    {},
                )
            )
        return tuple(
            f"{category}/{name}"
            for category, items
            in self._providers.items()
            for name in items
        )

    def categories(self) -> tuple[str, ...]:
        return tuple(self._providers)

    def ready(self) -> bool:
        return all(
            provider.ready()
            for items in self._providers.values()
            for provider in items.values()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "categories": self.categories(),
            "providers": self.names(),
            "ready": self.ready(),
        }


__all__ = [
    "ProviderRegistry",
]
