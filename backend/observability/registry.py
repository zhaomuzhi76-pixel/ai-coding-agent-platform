"""Global singleton registry for observability.

让所有层（platform / mcp / lsp / api）共用同一个 Tracer / AlertManager。
"""
from __future__ import annotations

from typing import Optional

from backend.observability.alert import AlertManager
from backend.observability.tracer import Tracer

_TRACER: Optional[Tracer] = None
_ALERTS: Optional[AlertManager] = None


def get_tracer() -> Tracer:
    global _TRACER
    if _TRACER is None:
        _TRACER = Tracer()
    return _TRACER


def get_alert_manager() -> AlertManager:
    global _ALERTS
    if _ALERTS is None:
        _ALERTS = AlertManager()
    return _ALERTS


def reset() -> None:
    global _TRACER, _ALERTS
    _TRACER = None
    _ALERTS = None


__all__ = ["get_tracer", "get_alert_manager", "reset"]
