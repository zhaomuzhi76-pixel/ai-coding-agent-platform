"""Factory: build the observability router for app assembly."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.observability.binding import ObservabilityBinding
from backend.api.observability.router import ObservabilityRouter


def build_observability_router() -> APIRouter:
    """Return an APIRouter ready for create_application(routers=...)."""
    return ObservabilityRouter(ObservabilityBinding()).router


__all__ = ["build_observability_router"]
