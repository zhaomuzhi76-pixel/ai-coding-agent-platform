from __future__ import annotations

from backend.runtime.plugin.capability import RuntimeCapability
from backend.runtime.plugins.dag_engine.provider import (
    DAGExecutionEngineProvider,
)


class DAGExecutionPlugin:
    """
    Builtin DAG execution plugin.

    Responsibility:
        - expose plugin identity
        - publish execution capability
        - register the execution provider

    Not Responsible:
        - execution dependency construction
        - scheduler construction
        - DAG construction
        - execution context construction
        - execution engine construction
    """

    VERSION = "2.1"

    name = "dag_engine"
    version = VERSION

    def capabilities(self) -> list[RuntimeCapability]:
        return [
            RuntimeCapability(
                category="execution",
                name="engine",
                version=self.VERSION,
            )
        ]

    def register(self, registry) -> None:
        if registry is None:
            raise ValueError(
                "capability registry required"
            )

        registry.register(
            RuntimeCapability(
                category="execution",
                name="engine",
                version=self.VERSION,
            ),
            DAGExecutionEngineProvider(
                registry,
            ),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": tuple(
                capability.key()
                for capability in self.capabilities()
            ),
            "ready": self.ready(),
        }


__all__ = [
    "DAGExecutionPlugin",
]
