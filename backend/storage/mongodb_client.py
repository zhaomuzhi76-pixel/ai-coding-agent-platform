from __future__ import annotations

from pymongo import MongoClient

from backend.storage.mongodb_config import MongoDBConfig


class MongoDBClient:
    VERSION = "2.0"

    def __init__(
        self,
        config: MongoDBConfig,
    ) -> None:
        if not isinstance(config, MongoDBConfig):
            raise TypeError("config must be MongoDBConfig")
        self.config = config
        self._client: MongoClient | None = None

    def connect(self) -> MongoClient:
        if self._client is None:
            self._client = MongoClient(self.config.uri)
        return self._client

    @property
    def client(self) -> MongoClient:
        return self.connect()

    @property
    def database(self):
        return self.client[self.config.database]

    def ping(self) -> bool:
        try:
            self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def health_check(self) -> bool:
        return self.ping()

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def dump(self) -> dict:
        return {
            "name": "MongoDBClient",
            "version": self.VERSION,
            "config": self.config.dump(),
            "connected": self._client is not None,
        }


__all__ = ["MongoDBClient"]
