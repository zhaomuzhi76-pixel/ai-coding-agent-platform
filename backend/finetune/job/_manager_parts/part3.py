"""Part 3 of manager.py."""
from __future__ import annotations
from .part1 import (Callable, OnEvent,)  # noqa
from .part2 import get_job_manager  # noqa

def reset_job_manager() -> None:
    """测试用：清单例。"""
    global _manager
    _manager = None

__all__ = [
    "JobManager",
    "OnEvent",
    "get_job_manager",
    "reset_job_manager",
    "subscribe_events",
    "unsubscribe_events",
]

def subscribe_events(listener: OnEvent) -> Callable[[], None]:
    return get_job_manager().subscribe(listener)

def unsubscribe_events(listener: OnEvent) -> None:
    mgr = get_job_manager()
    try: mgr._listeners.remove(listener)
    except ValueError: pass
