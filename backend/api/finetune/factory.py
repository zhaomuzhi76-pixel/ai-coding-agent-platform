"""Factory: build the finetune router for app assembly."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.finetune.binding import FinetuneBinding
from backend.api.finetune.router import FinetuneRouter


def build_finetune_router() -> APIRouter:
    return FinetuneRouter(FinetuneBinding()).router


__all__ = ["build_finetune_router"]
