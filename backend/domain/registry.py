"""DomainRegistry: register + resolve DomainProvider by name."""
from __future__ import annotations

from typing import Dict, List

from backend.domain.contracts import DomainProvider


class DomainRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, DomainProvider] = {}

    def register(self, provider: DomainProvider) -> None:
        name = getattr(provider, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise TypeError("provider.name must be non-empty str")
        self._providers[name.strip()] = provider

    def register_all(self, providers: List[DomainProvider]) -> None:
        for p in providers:
            self.register(p)

    def resolve(self, name: str) -> DomainProvider:
        if name not in self._providers:
            raise KeyError(
                f"domain not registered: {name} "
                f"(available {sorted(self._providers)})"
            )
        return self._providers[name]

    def has(self, name: str) -> bool:
        return name in self._providers

    def names(self) -> List[str]:
        return sorted(self._providers.keys())

    def ready(self) -> bool:
        return all(p.ready() for p in self._providers.values())

    def dump(self) -> Dict:
        return {
            "ready": self.ready(),
            "domains": self.names(),
            "count": len(self._providers),
        }
