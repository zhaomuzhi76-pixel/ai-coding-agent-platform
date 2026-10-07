"""PlatformServerRegistration: register platform router on FastAPI app."""
from __future__ import annotations

from typing import Any, Dict, Tuple

from fastapi import FastAPI

from backend.api.platform.binding import PlatformBinding
from backend.api.platform.router import PlatformRouter


class PlatformServerRegistration:
    VERSION = "1.0"

    def register(
        self,
        app: FastAPI,
        binding: PlatformBinding,
    ) -> Tuple[object, ...]:
        if not isinstance(app, FastAPI):
            raise TypeError("app must FastAPI")
        if not isinstance(binding, PlatformBinding):
            raise TypeError("binding must PlatformBinding")
        router = PlatformRouter(binding)
        if not router.ready():
            raise RuntimeError("platform router unavailable")
        app.include_router(router.router)
        return (router,)

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["PlatformServerRegistration"]
