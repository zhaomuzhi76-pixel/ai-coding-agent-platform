"""WSAgentHandlerFactory: 构造 WS Agent handler（走 platform）。"""
from __future__ import annotations

from typing import Any

from backend.api.ws_agent_handler import WSAgentHandler
from backend.api.ws_platform_coordinator import (
    PlatformBackedCoordinator,
)


class WSAgentHandlerFactory:
    VERSION = "4.0"

    def create(self, **kwargs: Any) -> WSAgentHandler:
        coordinator = PlatformBackedCoordinator()
        handler = WSAgentHandler(coordinator=coordinator)
        if not handler.ready():
            raise RuntimeError("websocket agent handler unavailable")
        return handler

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["WSAgentHandlerFactory"]
