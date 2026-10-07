from __future__ import annotations

from backend.storage.mongodb.mongo_connection_settings import (
    MongoConnectionSettings,
)


class MongoDBConfig:
    VERSION = "1.1"

    def __init__(
        self,
        uri: str | None = None,
        database: str | None = None,
    ) -> None:
        settings = (
            MongoConnectionSettings.from_environment()
        )

        self.uri = (
            uri.strip()
            if uri is not None
            else settings.uri
        )
        self.database = (
            database.strip()
            if database is not None
            else settings.database
        )

        if not self.uri:
            raise ValueError(
                "MongoDB URI required"
            )

        if not self.database:
            raise ValueError(
                "MongoDB database required"
            )

    def dump(self) -> dict[str, str]:
        return {
            "name": "MongoDBConfig",
            "version": self.VERSION,
            "uri": self.uri,
            "database": self.database,
        }


__all__ = ["MongoDBConfig"]
