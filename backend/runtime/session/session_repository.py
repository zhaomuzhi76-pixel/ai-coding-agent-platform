"""
Runtime Session Repository Contract

Responsibility:

    - runtime session persistence contract
    - session entity storage access


Responsible:

    - create session
    - load session
    - delete session
    - query runtime binding


Not Responsible:

    - runtime state persistence
    - event persistence
    - result persistence
    - execution lifecycle
    - recovery
    - database implementation
"""


from __future__ import annotations


from typing import Protocol


from backend.runtime.session.session_model import (
    RuntimeSession,
)



class SessionRepository(
    Protocol,
):

    """
    Storage abstraction for RuntimeSession.

    Implementations:

        - MemorySessionRepository
        - MongoSessionRepository
        - PostgresSessionRepository

    """


    VERSION = "6.0"



    async def create(
        self,
        session: RuntimeSession,
    ) -> None:
        """
        Persist session entity.
        """

        ...



    async def get_by_session_id(
        self,
        session_id: str,
    ) -> RuntimeSession | None:
        """
        Load session by session identity.
        """

        ...



    async def get_by_runtime_id(
        self,
        runtime_id: str,
    ) -> RuntimeSession | None:
        """
        Load session by bound runtime identity.
        """

        ...



    async def delete_by_session_id(
        self,
        session_id: str,
    ) -> bool:
        """
        Delete session entity.
        """

        ...



__all__ = [
    "SessionRepository",
]
