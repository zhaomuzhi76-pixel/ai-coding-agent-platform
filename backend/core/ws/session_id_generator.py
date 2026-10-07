from __future__ import annotations

from typing import Final
from uuid import uuid4


class SessionIdGenerator:
    """
    Session identifier generator.

    Responsibility:

        - generate unique session identifiers

    Not Responsible:

        - connection management
        - session storage
        - authentication
        - lifecycle
        - business logic
    """

    VERSION: Final = "2.0"

    RESPONSIBILITY: Final = (
        "session_id_generation",
    )

    PREFIX: Final = "session-"

    def generate(
        self,
    ) -> str:

        return (
            self.PREFIX
            + uuid4().hex[:12]
        )


__all__ = [
    "SessionIdGenerator",
]
