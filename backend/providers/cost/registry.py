"""Cost registry: 全局单例。"""
from __future__ import annotations

from typing import Optional

from backend.providers.cost.tracker import CostTracker

_TRACKER: Optional[CostTracker] = None


def get_tracker() -> CostTracker:
    global _TRACKER
    if _TRACKER is None:
        _TRACKER = CostTracker()
    return _TRACKER


def reset() -> None:
    global _TRACKER
    _TRACKER = None


__all__ = ["get_tracker", "reset"]
