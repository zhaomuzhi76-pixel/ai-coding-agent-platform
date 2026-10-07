from __future__ import annotations

from enum import Enum


class ProjectSessionRuntimeState(
    str,
    Enum,
):
    """
    Runtime lifecycle state for a project session.

    Owns only runtime lifecycle state.
    """

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"

    def ready(
        self,
    ) -> bool:
        return (
            self
            is ProjectSessionRuntimeState.ACTIVE
        )


__all__ = [
    "ProjectSessionRuntimeState",
]
