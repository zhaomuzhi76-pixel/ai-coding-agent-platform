from __future__ import annotations

from backend.agent.capability.capability_contract import (
    CapabilityContract,
)


class CapabilityRegistry:
    """
    Capability registration boundary.

    Responsibility:
        - register capability
        - validate capability identity
        - reject duplicate identities
        - lookup capability
        - project readiness

    Does not own:
        - capability execution
        - runtime construction
        - transport
        - persistence
    """

    VERSION = "2.0"

    def __init__(self) -> None:
        self._items: dict[
            str,
            CapabilityContract,
        ] = {}

    def register(
        self,
        capability: CapabilityContract,
    ) -> None:
        self._validate(capability)

        name = capability.name().strip()

        if name in self._items:
            raise ValueError(
                f"capability already registered: {name}"
            )

        self._items[name] = capability

    def get(
        self,
        name: str,
    ) -> CapabilityContract | None:
        if not isinstance(name, str):
            return None

        return self._items.get(name.strip())

    def names(self) -> tuple[str, ...]:
        return tuple(self._items)

    def capabilities(
        self,
    ) -> tuple[CapabilityContract, ...]:
        return tuple(self._items.values())

    def ready(self) -> bool:
        return all(
            capability.ready()
            for capability in self._items.values()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "count": len(self._items),
            "names": self.names(),
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        capability: CapabilityContract,
    ) -> None:
        if not isinstance(
            capability,
            CapabilityContract,
        ):
            raise TypeError(
                "capability must implement CapabilityContract"
            )

        name = capability.name()

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "capability name required"
            )

        if not callable(
            getattr(capability, "ready", None)
        ):
            raise TypeError(
                f"capability ready missing: {name}"
            )


__all__ = [
    "CapabilityRegistry",
]
