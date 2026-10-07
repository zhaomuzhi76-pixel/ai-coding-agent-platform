from __future__ import annotations

from fastapi import FastAPI

from backend.api.http_entry.fastapi_http_runtime_entry_contract import (
    FastAPIHTTPRuntimeEntryContract,
)


class FastAPIHTTPEntryLifespanIntegrationSupport:
    """
    Validation support for the HTTP-entry/lifespan bridge.

    Owns validation only.

    The integration consumes the frozen HTTP runtime entry contract
    directly. Router construction remains owned by the HTTP entry.
    """

    VERSION = "1.3"

    @staticmethod
    def validate_application(
        application: object,
    ) -> FastAPI:
        if not isinstance(application, FastAPI):
            raise TypeError("application must FastAPI")
        return application

    @staticmethod
    def validate_entry(
        entry: object,
    ) -> FastAPIHTTPRuntimeEntryContract:
        if not isinstance(
            entry,
            FastAPIHTTPRuntimeEntryContract,
        ):
            raise TypeError(
                "entry must implement "
                "FastAPIHTTPRuntimeEntryContract"
            )

        if not entry.ready():
            raise RuntimeError(
                "http runtime entry not ready"
            )

        return entry

    @staticmethod
    def validate_startup(
        startup: object,
    ) -> object:
        if startup is None:
            raise ValueError("startup required")

        if getattr(
            startup,
            "runtime_submission",
            None,
        ) is None:
            raise RuntimeError(
                "runtime submission unavailable"
            )

        return startup

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIHTTPEntryLifespanIntegrationSupport",
]
