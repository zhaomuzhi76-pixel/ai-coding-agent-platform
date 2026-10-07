from __future__ import annotations

from collections.abc import Callable

from backend.process_control.process_control import (
    ProcessControl,
)
from backend.process_control.process_control_support import (
    ProcessControlSupport,
)


class ProcessControlFactory:
    """
    Sole construction owner for process control.

    Owns only:
        - runner resolution
        - ProcessControl construction
        - construction-time readiness validation

    The runner is an injected lower-layer capability. This factory
    never constructs or imports process-main orchestration.
    """

    VERSION = "1.1"

    def create(
        self,
        *,
        runner: Callable[[], object] | None = None,
        support: ProcessControlSupport | None = None,
    ) -> ProcessControl:
        active_runner = runner or self._idle_runner

        control = ProcessControl(
            runner=active_runner,
            support=support,
        )

        if not control.ready():
            raise RuntimeError(
                "process control unavailable"
            )

        return control

    @staticmethod
    def _idle_runner() -> int:
        return 0

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
    "ProcessControlFactory",
]
