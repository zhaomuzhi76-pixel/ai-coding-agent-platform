from __future__ import annotations

from fastapi import FastAPI

from backend.api.code_intelligence.registration import (
    CodeIntelligenceServerRegistration,
)


class CodeIntelligenceServerLifecycle:
    VERSION = "1.0"

    def __init__(
        self,
        registration: CodeIntelligenceServerRegistration | None = None,
    ) -> None:
        self.registration = (
            registration
            or CodeIntelligenceServerRegistration()
        )

    def register(
        self,
        app: FastAPI,
        startup: object,
    ) -> None:
        self.registration.register(app, startup)

        if not self.registration.registered():
            raise RuntimeError(
                "code intelligence server registration unavailable"
            )

    def unregister(self, app: FastAPI) -> None:
        self.registration.unregister(app)

    def registered(self) -> bool:
        return self.registration.registered()

    def ready(self) -> bool:
        return self.registration.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "registered": self.registered(),
            "registration": self.registration.dump(),
        }


__all__ = ["CodeIntelligenceServerLifecycle"]
