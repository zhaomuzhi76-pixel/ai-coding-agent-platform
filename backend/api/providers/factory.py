"""Provider router factory."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.providers.binding import ProviderBinding
from backend.api.providers.router import ProviderRouter


def build_provider_router() -> APIRouter:
    return ProviderRouter(ProviderBinding()).router


__all__ = ["build_provider_router"]
