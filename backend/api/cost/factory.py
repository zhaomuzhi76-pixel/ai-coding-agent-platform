"""Cost router factory."""
from __future__ import annotations

from fastapi import APIRouter

from backend.api.cost.binding import CostBinding
from backend.api.cost.router import CostRouter


def build_cost_router() -> APIRouter:
    return CostRouter(CostBinding()).router


__all__ = ["build_cost_router"]
