from __future__ import annotations

from enum import Enum


class ProjectSessionState(
    str,
    Enum,
):
    """
    Logical project-session lifecycle state.

    CREATED:
        constructed and valid, awaiting activation.

    ACTIVE:
        activated and valid for operational admission.

    CLOSED:
        lifecycle terminated and no longer ready.
    """

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"

    def ready(
        self,
    ) -> bool:
        return self in (
            ProjectSessionState.CREATED,
            ProjectSessionState.ACTIVE,
        )


__all__ = [
    "ProjectSessionState",
]
