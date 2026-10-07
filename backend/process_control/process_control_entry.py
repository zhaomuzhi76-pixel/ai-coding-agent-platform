from __future__ import annotations

from backend.process_control.process_control_factory import (
    ProcessControlFactory,
)


VERSION = "1.2"


def run_control() -> int:
    """
    Internal process-control projection.

    ProcessControl construction remains owned by
    ProcessControlFactory.

    This module is not a second public process main.
    """

    control = (
        ProcessControlFactory()
        .create()
    )

    return control.run()


__all__ = [
    "VERSION",
    "run_control",
]
