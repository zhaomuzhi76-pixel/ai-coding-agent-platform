from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from backend.storage.redis_config import RedisConfig
from backend.storage.redis_health import RedisHealth


class RedisClient:
    VERSION = "4.0"

    def __init__(
        self,
        config: RedisConfig,
    ) -> None:
        if not isinstance(config, RedisConfig):
            raise TypeError("config must be RedisConfig")
        self.config = config
        self.client = redis.from_url(
            self.config.url,
            encoding="utf-8",
            decode_responses=True,
        )
        self.health_checker = RedisHealth(self.client)

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> bool:
        data = json.dumps(value, ensure_ascii=False)
        return bool(
            await self.client.set(key, data, ex=expire)
        )

    async def get(self, key: str) -> Any | None:
        value = await self.client.get(key)
        return None if value is None else json.loads(value)

    async def delete(self, key: str) -> bool:
        return (await self.client.delete(key)) > 0

    async def exists(self, key: str) -> bool:
        return (await self.client.exists(key)) > 0

    async def ping(self) -> bool:
        return bool(await self.client.ping())

    async def health(self) -> dict[str, object]:
        return await self.health_checker.report()

    async def close(self) -> None:
        close = getattr(self.client, "aclose", None)
        if close is not None:
            await close()
            return
        await self.client.close()

    def dump(self) -> dict[str, object]:
        return {
            "name": "RedisClient",
            "version": self.VERSION,
            "config": self.config.dump(),
            "health": self.health_checker.dump(),
        }


__all__ = ["RedisClient"]
