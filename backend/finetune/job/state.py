"""任务状态机（L0 · 纯逻辑）。

职责：
    - 定义 JobState 枚举
    - 定义合法状态转移
    - 判断终态

不负责：
    - 任务数据（spec 管）
    - 事件（event 管）
    - 持久化（store 管）

状态图：
    pending → running → succeeded
                     ↘ failed
                     ↘ cancelled
    pending ↘ cancelled（未启动即可取消）
    pending ↘ failed（如数据加载失败）
"""
from __future__ import annotations

from enum import Enum


class JobState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


_TERMINAL: frozenset[JobState] = frozenset({
    JobState.SUCCEEDED,
    JobState.FAILED,
    JobState.CANCELLED,
})

_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.PENDING: frozenset({
        JobState.RUNNING,
        JobState.CANCELLED,
        JobState.FAILED,
    }),
    JobState.RUNNING: frozenset({
        JobState.SUCCEEDED,
        JobState.FAILED,
        JobState.CANCELLED,
    }),
    JobState.SUCCEEDED: frozenset(),
    JobState.FAILED: frozenset(),
    JobState.CANCELLED: frozenset(),
}


def is_terminal(state: JobState) -> bool:
    if not isinstance(state, JobState):
        raise TypeError("state must JobState")
    return state in _TERMINAL


def can_transition(src: JobState, dst: JobState) -> bool:
    if not isinstance(src, JobState) or not isinstance(dst, JobState):
        raise TypeError("both must JobState")
    return dst in _TRANSITIONS.get(src, frozenset())


def validate_transition(src: JobState, dst: JobState) -> None:
    if not can_transition(src, dst):
        raise ValueError(f"invalid transition: {src.value} -> {dst.value}")


def all_states() -> tuple[str, ...]:
    return tuple(s.value for s in JobState)


__all__ = [
    "JobState",
    "is_terminal",
    "can_transition",
    "validate_transition",
    "all_states",
]
