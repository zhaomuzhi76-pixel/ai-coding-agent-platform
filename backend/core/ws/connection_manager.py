from __future__ import annotations

from backend.core.contracts.value import CoreValue

from backend.core.ws.connection_protocol import (
    ConnectionProtocol,
)
from backend.core.ws.connection_registry import (
    ConnectionRegistry,
)
from backend.core.ws.session_id_generator import (
    SessionIdGenerator,
)


class ConnectionManager:
    """
    WebSocket connection operations.

    Responsibility:
        - accept managed connections
        - send messages to managed connections
        - broadcast messages to managed connections
        - disconnect managed connections
        - close and clear all managed connections

    Not Responsible:
        - connection storage
        - session ID generation
        - authentication
        - message construction
        - agent execution
        - persistence
    """

    VERSION = "5.1"

    RESPONSIBILITY = (
        "websocket_connection_operations",
    )

    def __init__(
        self,
        registry: ConnectionRegistry,
        session_id_generator: SessionIdGenerator,
    ) -> None:
        if not isinstance(
            registry,
            ConnectionRegistry,
        ):
            raise TypeError(
                "registry must be ConnectionRegistry"
            )

        if not isinstance(
            session_id_generator,
            SessionIdGenerator,
        ):
            raise TypeError(
                "session_id_generator must be SessionIdGenerator"
            )

        self._registry = registry
        self._session_id_generator = session_id_generator

    async def connect(
        self,
        connection: ConnectionProtocol,
    ) -> str:
        if not isinstance(
            connection,
            ConnectionProtocol,
        ):
            raise TypeError(
                "connection must implement ConnectionProtocol"
            )

        await connection.accept()

        session_id = (
            self._session_id_generator.generate()
        )

        self._registry.register(
            session_id,
            connection,
        )

        return session_id

    def disconnect(
        self,
        session_id: str,
    ) -> None:
        self._registry.remove(
            session_id
        )

    async def close_all(self) -> None:
        sessions = self._registry.sessions()

        for session_id in sessions:
            connection = self._registry.get(
                session_id
            )

            if connection is None:
                continue

            try:
                await connection.close()
            except Exception:
                pass

        self._registry.clear()

    async def send_to_session(
        self,
        session_id: str,
        message: dict[str, CoreValue],
    ) -> bool:
        connection = self._registry.get(
            session_id
        )

        if connection is None:
            return False

        try:
            await connection.send(
                message
            )
        except Exception:
            self.disconnect(
                session_id
            )
            return False

        return True

    async def broadcast(
        self,
        message: dict[str, CoreValue],
    ) -> None:
        disconnected: list[str] = []

        for session_id in (
            self._registry.sessions()
        ):
            connection = self._registry.get(
                session_id
            )

            if connection is None:
                continue

            try:
                await connection.send(
                    message
                )
            except Exception:
                disconnected.append(
                    session_id
                )

        for session_id in disconnected:
            self.disconnect(
                session_id
            )

    def has_session(
        self,
        session_id: str,
    ) -> bool:
        return self._registry.has(
            session_id
        )

    def count(
        self,
    ) -> int:
        return self._registry.count()

    def ready(
        self,
    ) -> bool:
        return self._registry.ready()

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": "ConnectionManager",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "connections": self.count(),
        }


__all__ = [
    "ConnectionManager",
]
