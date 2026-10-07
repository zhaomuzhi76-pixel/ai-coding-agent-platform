"""L1 排序模型状态与探测结果枚举。"""
from __future__ import annotations

from enum import Enum


class ModelStatus(str, Enum):
    UNTESTED = "untested"
    PROBING = "probing"
    PASSING = "passing"
    FAILING = "failing"
    DISABLED = "disabled"

    @property
    def selectable(self) -> bool:
        return self is ModelStatus.PASSING


class ProbeOutcome(str, Enum):
    OK = "ok"
    EMPTY_RESULT = "empty_result"
    BAD_SHAPE = "bad_shape"
    TIMEOUT = "timeout"
    EXCEPTION = "exception"
    NOT_AVAILABLE = "not_available"
