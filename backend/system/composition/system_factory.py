from __future__ import annotations

from backend.process_operations import (
    ProcessOperationsContract,
    ProcessOperationsFactory,
)
from backend.system.composition.process_operations_component import (
    ProcessOperationsComponent,
)
from backend.system.composition.system import (
    SystemComposition,
)


class SystemFactory:
    """
    Construction boundary for the canonical system composition.

    Owns only:
        - process operations construction
        - system component adaptation
        - SystemComposition construction

    Does not own:
        - process execution
        - system startup
        - system shutdown
        - lifecycle state transition
        - runtime execution
    """

    VERSION = "3.2"

    def create(
        self,
    ) -> SystemComposition:
        operations = (
            ProcessOperationsFactory()
            .create()
        )

        self._validate_operations(
            operations
        )

        component = ProcessOperationsComponent(
            operations
        )

        self._validate_component(
            component
        )

        system = SystemComposition(
            components=(component,),
        )

        self._validate_system(
            system
        )

        return system

    @staticmethod
    def _validate_operations(
        operations: object,
    ) -> None:
        if not isinstance(
            operations,
            ProcessOperationsContract,
        ):
            raise TypeError(
                "process operations contract required"
            )

        if not operations.ready():
            raise RuntimeError(
                "process operations unavailable"
            )

    @staticmethod
    def _validate_component(
        component: object,
    ) -> None:
        if not isinstance(
            component,
            ProcessOperationsComponent,
        ):
            raise TypeError(
                "process operations system component required"
            )

        if not component.ready():
            raise RuntimeError(
                "process operations system component unavailable"
            )

    @staticmethod
    def _validate_system(
        system: SystemComposition,
    ) -> None:
        for name in (
            "ready",
            "start",
            "stop",
            "snapshot",
            "dump",
        ):
            checker = getattr(
                system,
                name,
                None,
            )

            if not callable(checker):
                raise TypeError(
                    "system composition must expose "
                    f"{name}()"
                )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "SystemFactory",
]
