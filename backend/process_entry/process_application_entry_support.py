from __future__ import annotations

from fastapi import FastAPI


class ProcessApplicationEntrySupport:
    """
    Validation support for the process application entry.
    """

    VERSION = "1.0"

    @staticmethod
    def validate_application(
        application: object,
    ) -> FastAPI:
        if not isinstance(
            application,
            FastAPI,
        ):
            raise TypeError(
                "application must FastAPI"
            )

        return application

    @staticmethod
    def validate_runner(
        runner: object,
    ):
        if not callable(runner):
            raise TypeError(
                "runner must be callable"
            )

        return runner

    @staticmethod
    def validate_host(
        host: object,
    ) -> str:
        if not isinstance(
            host,
            str,
        ) or not host.strip():
            raise ValueError(
                "host required"
            )

        return host

    @staticmethod
    def validate_port(
        port: object,
    ) -> int:
        if not isinstance(
            port,
            int,
        ):
            raise TypeError(
                "port must int"
            )

        if port <= 0 or port > 65535:
            raise ValueError(
                "port must be valid TCP port"
            )

        return port

    @staticmethod
    def validate_log_level(
        log_level: object,
    ) -> str:
        if not isinstance(
            log_level,
            str,
        ) or not log_level.strip():
            raise ValueError(
                "log level required"
            )

        return log_level.lower()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProcessApplicationEntrySupport",
]
