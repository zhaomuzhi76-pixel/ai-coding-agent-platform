from __future__ import annotations

from collections.abc import Iterable

from backend.system.contracts.system_contract import (
    SystemHealth,
    SystemReadiness,
    SystemSnapshot,
    SystemState,
)
from backend.system.health.aggregator import (
    SystemHealthAggregator,
)
from backend.system.lifecycle.coordinator import (
    SystemLifecycleCoordinator,
)
from backend.system.plugin.extension_host import (
    SystemExtensionHost,
)


class SystemComposition:
    """
    System-level composition boundary.

    Composes already-built system governance components.
    It does not construct application subsystems.
    """

    VERSION = "1.1"

    def __init__(
        self,
        *,
        components: Iterable[object] | None = None,
        extensions: Iterable[object] | None = None,
        context=None,
    ) -> None:
        component_tuple = tuple(
            component
            for component in (components or ())
            if component is not None
        )

        self.lifecycle = SystemLifecycleCoordinator(
            components=component_tuple,
        )
        self.health = SystemHealthAggregator(
            components=component_tuple,
            state_provider=lambda: self.lifecycle.state,
        )
        self.extensions = SystemExtensionHost(
            extensions=extensions,
            context=context,
        )

    def start(self) -> None:
        self.lifecycle.start()

        try:
            self.extensions.attach_all()
        except Exception:
            self.lifecycle.fail()
            raise

        if not self.ready():
            self.lifecycle.fail()
            self.extensions.detach_all()
            raise RuntimeError(
                "system composition unavailable"
            )

    def stop(self) -> None:
        self.extensions.detach_all()
        self.lifecycle.stop()

    def ready(self) -> bool:
        return (
            self.lifecycle.ready()
            and self.health.ready()
            and self.extensions.ready()
        )

    def state(self) -> SystemState:
        return self.lifecycle.state

    def health_snapshot(self) -> SystemHealth:
        return self.health.evaluate()

    def readiness(self) -> SystemReadiness:
        return SystemReadiness(
            ready=self.lifecycle.ready(),
            state=self.state(),
            reason=None,
        )

    def snapshot(self) -> SystemSnapshot:
        return SystemSnapshot(
            state=self.state(),
            readiness=self.readiness(),
            health=self.health_snapshot(),
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "state": self.state().value,
            "ready": self.ready(),
            "lifecycle": self.lifecycle.dump(),
            "health": self.health.dump(),
            "extensions": self.extensions.dump(),
        }


__all__ = [
    "SystemComposition",
]
