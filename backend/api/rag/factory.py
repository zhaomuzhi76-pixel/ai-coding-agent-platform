"""Factory: build the RAG router for app assembly."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.rag.binding import RagBinding
from backend.api.rag.router import RagRouter


def build_rag_router() -> APIRouter:
    return RagRouter(RagBinding()).router


__all__ = ["build_rag_router"]
