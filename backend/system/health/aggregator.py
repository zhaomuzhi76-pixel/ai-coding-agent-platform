from __future__ import annotations

from collections.abc import Iterable, Mapping

from backend.system.contracts.system_contract import (
    SystemComponentProtocol,
    SystemHealth,
    SystemState,
)


class SystemHealthAggregator:
    VERSION = "2.0"

    def __init__(
        self,
        components: Iterable[SystemComponentProtocol] | None = None,
        state_provider=None,
    ) -> None:
        self._components = tuple(
            component
            for component in (components or ())
            if component is not None
        )
        self._state_provider = state_provider

        for component in self._components:
            if not isinstance(
                component,
                SystemComponentProtocol,
            ):
                raise TypeError(
                    "invalid system component"
                )

    def evaluate(self) -> SystemHealth:
        components = self._component_health()
        healthy = all(components.values())

        return SystemHealth(
            healthy=healthy,
            state=self._state(),
            components=components,
            reason=(
                None
                if healthy
                else "one or more system components unhealthy"
            ),
        )

    def ready(self) -> bool:
        return self.evaluate().healthy

    def dump(self) -> dict[str, object]:
        health = self.evaluate()

        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "healthy": health.healthy,
            "state": health.state.value,
            "components": dict(health.components),
            "reason": health.reason,
        }

    def _component_health(self) -> Mapping[str, bool]:
        return {
            component.name: component.ready()
            for component in self._components
        }

    def _state(self) -> SystemState:
        if self._state_provider is None:
            return (
                SystemState.READY
                if self.ready_components()
                else SystemState.FAILED
            )

        state = self._state_provider()

        if isinstance(state, SystemState):
            return state

        raise TypeError(
            "state provider must return SystemState"
        )

    def ready_components(self) -> bool:
        return all(
            component.ready()
            for component in self._components
        )


__all__ = [
    "SystemHealthAggregator",
]
