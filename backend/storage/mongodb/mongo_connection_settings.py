from __future__ import annotations
from backend.config.constants.endpoints import (
    MONGODB_URL,
)

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus, urlsplit, urlunsplit

from backend.storage.environment.environment_loader import (
    EnvironmentLoader,
)


@dataclass(frozen=True, slots=True)
class MongoConnectionSettings:
    uri: str
    database: str

    @classmethod
    def from_environment(
        cls,
    ) -> "MongoConnectionSettings":
        EnvironmentLoader(
            Path.cwd(),
        ).load()

        database = (
            os.getenv("MONGO_DATABASE")
            or os.getenv("MONGODB_DATABASE")
            or "agent"
        ).strip()

        uri = (
            os.getenv("MONGO_URL")
            or os.getenv("MONGODB_URL")
            or MONGODB_URL
        ).strip()

        user = os.getenv(
            "MONGO_USER",
            "",
        ).strip()
        password = os.getenv(
            "MONGO_PASSWORD",
            "",
        ).strip()
        auth_source = os.getenv(
            "MONGO_AUTH_SOURCE",
            "admin",
        ).strip()

        if user and password:
            uri = cls._apply_auth(
                uri,
                user,
                password,
                auth_source,
            )

        if not uri:
            raise ValueError(
                "MongoDB URI required"
            )

        if not database:
            raise ValueError(
                "MongoDB database required"
            )

        return cls(
            uri=uri,
            database=database,
        )

    @staticmethod
    def _apply_auth(
        uri: str,
        user: str,
        password: str,
        auth_source: str,
    ) -> str:
        parsed = urlsplit(uri)

        if parsed.scheme != "mongodb":
            raise ValueError(
                "MongoDB URI scheme must mongodb"
            )

        host = parsed.hostname
        port = parsed.port

        if not host:
            raise ValueError(
                "MongoDB host required"
            )

        netloc = (
            f"{quote_plus(user)}:"
            f"{quote_plus(password)}@"
            f"{host}"
        )

        if port is not None:
            netloc += f":{port}"

        query_parts = [
            item
            for item in parsed.query.split("&")
            if item
            and not item.startswith("authSource=")
        ]
        query_parts.append(
            "authSource="
            + quote_plus(auth_source)
        )

        return urlunsplit(
            (
                parsed.scheme,
                netloc,
                parsed.path,
                "&".join(query_parts),
                parsed.fragment,
            )
        )

    def ready(self) -> bool:
        return bool(
            self.uri.strip()
            and self.database.strip()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": "1.2",
            "database": self.database,
            "uri_authenticated": (
                "@"
                in self.uri.split(
                    "://",
                    1,
                )[-1]
            ),
            "ready": self.ready(),
        }


__all__ = [
    "MongoConnectionSettings",
]
