"""Factory: build the security router for app assembly."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.security.binding import SecurityBinding
from backend.api.security.router import SecurityRouter


def build_security_router() -> APIRouter:
    return SecurityRouter(SecurityBinding()).router


__all__ = ["build_security_router"]
