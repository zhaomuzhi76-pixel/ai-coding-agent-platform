from __future__ import annotations

import os


class RedisConfig:
    VERSION = "2.0"

    def __init__(
        self,
        url: str | None = None,
    ) -> None:
        self.url = url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        )

        if not self.url.strip():
            raise ValueError("REDIS_URL required")

    def dump(self) -> dict[str, str]:
        return {
            "name": "RedisConfig",
            "version": self.VERSION,
            "url": self.url,
        }


__all__ = ["RedisConfig"]
