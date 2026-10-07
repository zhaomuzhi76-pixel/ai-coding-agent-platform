"""
Memory Runtime Session Repository

Responsibility:

    - in-memory RuntimeSession storage


Not Responsible:

    - runtime state persistence
    - event persistence
    - result persistence
    - execution lifecycle
    - recovery


This module implements:

    SessionRepository Protocol

Future replacements:

    MongoSessionRepository
    PostgresSessionRepository
"""


from __future__ import annotations


from backend.runtime.session.session_model import (
    RuntimeSession,
)

from backend.runtime.session.session_repository import (
    SessionRepository,
)



class MemorySessionRepository(
    SessionRepository,
):


    VERSION = "1.0"



    def __init__(
        self,
    ) -> None:

        self._sessions: dict[
            str,
            RuntimeSession,
        ] = {}

        self.create_count = 0
        self.delete_count = 0



    async def create(
        self,
        session: RuntimeSession,
    ) -> None:

        self._validate_session(
            session
        )

        self._sessions[
            session.session_id
        ] = session

        self.create_count += 1



    async def get_by_session_id(
        self,
        session_id: str,
    ) -> RuntimeSession | None:

        self._validate_id(
            session_id
        )

        return self._sessions.get(
            session_id
        )



    async def get_by_runtime_id(
        self,
        runtime_id: str,
    ) -> RuntimeSession | None:

        self._validate_id(
            runtime_id
        )

        for session in self._sessions.values():

            if session.runtime_id == runtime_id:

                return session


        return None



    async def delete_by_session_id(
        self,
        session_id: str,
    ) -> bool:

        self._validate_id(
            session_id
        )

        if session_id not in self._sessions:

            return False


        del self._sessions[
            session_id
        ]

        self.delete_count += 1

        return True



    def ready(
        self,
    ) -> bool:

        return True



    def dump(
        self,
    ) -> dict:

        return {

            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "session_count":
                len(self._sessions),

            "create_count":
                self.create_count,

            "delete_count":
                self.delete_count,

        }



    def _validate_session(
        self,
        session: RuntimeSession,
    ) -> None:

        if not isinstance(
            session,
            RuntimeSession,
        ):

            raise TypeError(
                "session must be RuntimeSession"
            )



    def _validate_id(
        self,
        value: str,
    ) -> None:

        if not value:

            raise ValueError(
                "id required"
            )



__all__ = [
    "MemorySessionRepository",
]
