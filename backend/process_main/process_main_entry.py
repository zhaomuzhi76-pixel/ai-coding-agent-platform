from __future__ import annotations

from typing import Callable

from backend.process_entry.process_application_entry import (
    ProcessApplicationEntry,
)
from backend.process_main.process_main_orchestrator_factory import (
    ProcessMainOrchestratorFactory,
)


VERSION = "2.5"


def main(
    *,
    application: object,
    runner: Callable | None = None,
) -> int:
    """
    Public process-entry projection.

    The outer executable owner supplies the application.
    """
    if application is None:
        raise ValueError(
            "application required"
        )

    return ProcessMainOrchestratorFactory().run(
        application=application,
        runner=runner,
    )


__all__ = [
    "VERSION",
    "main",
]
