"""可观测性插件 —— 内存环形缓冲的结构化事件。

职责：单一（emit / recent / clear）。
"""
from __future__ import annotations
from collections import deque
from typing import Any

_MAX = 500
_EVENTS: deque = deque(maxlen=_MAX)


def emit(name: str, **fields: Any) -> None:
    """写入一条结构化事件到环形缓冲（线程内不安全，够用）。"""
    _EVENTS.append({"name": name, **fields})


def recent(n: int = 20) -> list:
    """返回最近 n 条事件（默认 20）。"""
    return list(_EVENTS)[-n:]


def clear() -> None:
    """清空事件缓冲（测试用）。"""
    _EVENTS.clear()
