from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.ws.connection_protocol import (
    ConnectionProtocol,
)


class ConnectionRegistry:
    """
    Connection reference registry.

    Responsibility:

        - register connection references
        - retrieve connection references
        - remove connection references
        - expose registered session identifiers

    Not Responsible:

        - connection acceptance
        - message delivery
        - session ID generation
        - authentication
        - persistence
    """

    VERSION = "2.0"

    RESPONSIBILITY = (
        "websocket_connection_registry",
    )

    def __init__(
        self,
    ) -> None:

        self._connections: dict[
            str,
            ConnectionProtocol,
        ] = {}

    def register(
        self,
        session_id: str,
        connection: ConnectionProtocol,
    ) -> None:

        self._validate_session_id(
            session_id
        )

        if not isinstance(
            connection,
            ConnectionProtocol,
        ):
            raise TypeError(
                "connection must implement ConnectionProtocol"
            )

        if session_id in self._connections:
            raise ValueError(
                f"session already registered: {session_id}"
            )

        self._connections[
            session_id
        ] = connection

    def get(
        self,
        session_id: str,
    ) -> ConnectionProtocol | None:

        self._validate_session_id(
            session_id
        )

        return self._connections.get(
            session_id
        )

    def remove(
        self,
        session_id: str,
    ) -> None:

        self._validate_session_id(
            session_id
        )

        self._connections.pop(
            session_id,
            None,
        )

    def has(
        self,
        session_id: str,
    ) -> bool:

        self._validate_session_id(
            session_id
        )

        return session_id in self._connections

    def count(
        self,
    ) -> int:

        return len(
            self._connections
        )

    def sessions(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._connections.keys()
        )

    def clear(
        self,
    ) -> None:

        self._connections.clear()

    def ready(
        self,
    ) -> bool:

        return True

    def dump(
        self,
    ) -> dict[str, CoreValue]:

        return {
            "name": "ConnectionRegistry",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "count": self.count(),
            "sessions": self.sessions(),
        }

    @staticmethod
    def _validate_session_id(
        session_id: str,
    ) -> None:

        if not isinstance(
            session_id,
            str,
        ):
            raise TypeError(
                "session_id must be str"
            )

        if not session_id.strip():
            raise ValueError(
                "session_id required"
            )


__all__ = [
    "ConnectionRegistry",
]
