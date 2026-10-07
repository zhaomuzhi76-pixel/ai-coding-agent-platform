"""Transport protocol for MCP message exchange."""
from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Send / receive JSON-RPC message dicts (one message = one frame)."""

    async def send(self, message: Dict[str, Any]) -> None: ...

    async def receive(self) -> Optional[Dict[str, Any]]: ...

    async def close(self) -> None: ...

    def ready(self) -> bool: ...


__all__ = ["Transport"]
