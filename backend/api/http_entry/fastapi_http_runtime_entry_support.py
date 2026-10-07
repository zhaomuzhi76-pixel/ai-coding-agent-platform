from __future__ import annotations

from fastapi import FastAPI


class FastAPIHTTPRuntimeEntrySupport:
    """
    Validation support for the canonical FastAPI HTTP entry.

    Runtime validation uses explicit behavior checks so that
    structurally compatible lifecycle implementations and doubles
    are accepted without requiring concrete inheritance.
    """

    VERSION = "1.2"

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
    def validate_startup(
        startup: object,
    ) -> object:
        if startup is None:
            raise ValueError(
                "startup required"
            )

        ready = getattr(
            startup,
            "ready",
            None,
        )

        if not callable(ready):
            raise TypeError(
                "startup must expose ready()"
            )

        if not bool(
            ready()
        ):
            raise RuntimeError(
                "application startup not ready"
            )

        return startup

    @staticmethod
    def validate_lifecycle(
        lifecycle: object,
    ) -> object:
        if lifecycle is None:
            raise ValueError(
                "http lifecycle required"
            )

        required = (
            "register",
            "unregister",
            "registered",
            "ready",
            "dump",
        )

        missing = [
            name
            for name in required
            if not callable(
                getattr(
                    lifecycle,
                    name,
                    None,
                )
            )
        ]

        if missing:
            raise TypeError(
                "lifecycle missing required behavior: "
                + ", ".join(missing)
            )

        if not bool(
            lifecycle.ready()
        ):
            raise RuntimeError(
                "http lifecycle not ready"
            )

        return lifecycle

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "FastAPIHTTPRuntimeEntrySupport",
]
