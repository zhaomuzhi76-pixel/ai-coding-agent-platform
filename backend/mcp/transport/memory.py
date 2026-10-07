"""In-process memory transport: pair of queues (for tests / local)."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from backend.mcp.transport.base import Transport


class MemoryTransport:
    """One end of an in-memory pair."""

    def __init__(
        self,
        outgoing: "asyncio.Queue[Optional[Dict[str, Any]]]",
        incoming: "asyncio.Queue[Optional[Dict[str, Any]]]",
    ) -> None:
        self._outgoing = outgoing
        self._incoming = incoming
        self._closed = False

    async def send(self, message: Dict[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("transport closed")
        await self._outgoing.put(dict(message))

    async def receive(self) -> Optional[Dict[str, Any]]:
        if self._closed:
            return None
        item = await self._incoming.get()
        return item

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._outgoing.put(None)

    def ready(self) -> bool:
        return not self._closed


class TransportPair:
    """Two connected transports."""

    def __init__(self) -> None:
        q1: "asyncio.Queue[Optional[Dict[str, Any]]]" = asyncio.Queue()
        q2: "asyncio.Queue[Optional[Dict[str, Any]]]" = asyncio.Queue()
        self.client: Transport = MemoryTransport(q1, q2)
        self.server: Transport = MemoryTransport(q2, q1)

    def dump(self) -> Dict[str, Any]:
        return {
            "client_ready": self.client.ready(),
            "server_ready": self.server.ready(),
        }


__all__ = ["MemoryTransport", "TransportPair"]
