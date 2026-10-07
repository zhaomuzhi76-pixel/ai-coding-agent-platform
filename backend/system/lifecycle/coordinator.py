from __future__ import annotations

from collections.abc import Iterable, Mapping

from backend.core.system_lifecycle import SystemLifecycle
from backend.core.system_lifecycle_contract import (
    SystemLifecycleSnapshot,
)
from backend.system.contracts.system_contract import (
    SystemComponentProtocol,
    SystemState,
)


class SystemLifecycleCoordinator:
    VERSION = "2.0"

    def __init__(
        self,
        lifecycle: SystemLifecycle | None = None,
        components: Iterable[SystemComponentProtocol] | None = None,
    ) -> None:
        self.lifecycle = (
            lifecycle
            if lifecycle is not None
            else SystemLifecycle()
        )
        self._components = tuple(
            component
            for component in (components or ())
            if component is not None
        )

        for component in self._components:
            if not isinstance(
                component,
                SystemComponentProtocol,
            ):
                raise TypeError(
                    "invalid system component"
                )

    @property
    def state(self) -> SystemState:
        mapping = {
            SystemLifecycle.CREATED: SystemState.CREATED,
            SystemLifecycle.READY: SystemState.READY,
            SystemLifecycle.FAILED: SystemState.FAILED,
        }
        return mapping[self.lifecycle.state]

    def start(self) -> None:
        if self.ready():
            return

        if not self._components_ready():
            self.lifecycle.mark_failed()
            raise RuntimeError(
                "system components unavailable"
            )

        self.lifecycle.mark_started()

    def stop(self) -> None:
        if self.lifecycle.state == SystemLifecycle.READY:
            self.lifecycle = SystemLifecycle()

    def fail(self) -> None:
        self.lifecycle.mark_failed()

    def ready(self) -> bool:
        return (
            self.lifecycle.ready()
            and self._components_ready()
        )

    def snapshot(self) -> SystemLifecycleSnapshot:
        return self.lifecycle.status()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "state": self.state.value,
            "ready": self.ready(),
            "components": self._component_status(),
        }

    def _components_ready(self) -> bool:
        return all(
            component.ready()
            for component in self._components
        )

    def _component_status(self) -> Mapping[str, bool]:
        return {
            component.name: component.ready()
            for component in self._components
        }


__all__ = [
    "SystemLifecycleCoordinator",
]
