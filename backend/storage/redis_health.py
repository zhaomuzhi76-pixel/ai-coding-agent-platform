from __future__ import annotations

from typing import Any

from backend.core.health.status import HealthStatus


class RedisHealth:
    """
    Async Redis health capability.

    Responsibility:
        - execute Redis connectivity checks
        - expose structured health report

    Not Responsible:
        - client creation
        - CRUD operations
        - lifecycle ownership
        - monitoring transport
    """

    VERSION = "2.0"

    def __init__(
        self,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError("redis client required")
        self.client = client

    async def check(self) -> HealthStatus:
        try:
            await self.client.ping()
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY

    async def report(self) -> dict[str, object]:
        try:
            pong = await self.client.ping()
            return {
                "status": HealthStatus.HEALTHY.value,
                "redis": True,
                "ping": pong,
                "version": self.VERSION,
            }
        except Exception as error:
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "redis": False,
                "message": str(error),
                "version": self.VERSION,
            }

    def dump(self) -> dict[str, object]:
        return {
            "name": "RedisHealth",
            "version": self.VERSION,
        }


__all__ = [
    "RedisHealth",
]
