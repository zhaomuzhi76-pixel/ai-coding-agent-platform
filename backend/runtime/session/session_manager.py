from __future__ import annotations


import uuid

from typing import TYPE_CHECKING


from backend.runtime.session.session_model import (
    RuntimeSession,
)


if TYPE_CHECKING:

    from backend.runtime.session.session_repository import (
        SessionRepository,
    )



class RuntimeSessionManager:
    """
    Runtime session lifecycle boundary.

    Responsible:

        - create session
        - load session
        - remove session
        - bind runtime identity


    Not Responsible:

        - runtime persistence
        - event persistence
        - result persistence
        - execution lifecycle
    """


    VERSION = "6.0"


    RESPONSIBILITY = (
        "runtime_session_lifecycle_management",
    )



    def __init__(
        self,
        repository: SessionRepository | None = None,
    ) -> None:

        self.repository = repository

        self.create_count = 0

        self.remove_count = 0



    async def create_session(
        self,
        metadata: dict | None = None,
    ) -> RuntimeSession:

        session = RuntimeSession(
            session_id=self._generate_session_id(),
            runtime_id=self._generate_runtime_id(),
            metadata=metadata or {},
        )


        if self.repository:

            await self.repository.create(
                session
            )


        self.create_count += 1


        return session



    async def get_session(
        self,
        session_id: str,
    ) -> RuntimeSession | None:

        self._validate_id(
            session_id
        )


        if self.repository is None:

            return None


        return await self.repository.get_by_session_id(
            session_id
        )



    async def remove_session(
        self,
        session_id: str,
    ) -> bool:

        self._validate_id(
            session_id
        )


        if self.repository is None:

            return False


        removed = await self.repository.delete_by_session_id(
            session_id
        )


        if removed:

            self.remove_count += 1


        return removed



    def ready(
        self,
    ) -> bool:

        return self.repository is not None



    def dump(
        self,
    ) -> dict:

        return {

            "name":
                self.__class__.__name__,

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "create_count":
                self.create_count,

            "remove_count":
                self.remove_count,

            "repository":
                (
                    self.repository.__class__.__name__
                    if self.repository
                    else None
                ),
        }



    def _generate_session_id(
        self,
    ) -> str:

        return (
            "session_"
            +
            uuid.uuid4().hex
        )



    def _generate_runtime_id(
        self,
    ) -> str:

        return (
            "runtime_"
            +
            uuid.uuid4().hex
        )



    def _validate_id(
        self,
        value: str,
    ) -> None:

        if not value:

            raise ValueError(
                "session id required"
            )



__all__ = [
    "RuntimeSessionManager",
]
