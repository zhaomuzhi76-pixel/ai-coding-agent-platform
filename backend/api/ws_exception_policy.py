"""WSExceptionPolicy: WebSocket 异常分类策略。

Owns: 异常类型 → 处置动作映射 / recoverable vs fatal 判定
Not:  WS 实际发送 / 连接管理 / 消息路由
"""
from __future__ import annotations


class WSExceptionPolicy:
    VERSION = "1.0"

    RECOVERABLE = (ValueError, TypeError, KeyError, AttributeError, LookupError)
    FATAL = (SystemExit, MemoryError, KeyboardInterrupt)

    def classify(self, exc: BaseException) -> str:
        if isinstance(exc, self.FATAL): return "fatal"
        if isinstance(exc, self.RECOVERABLE): return "recoverable"
        return "unknown"

    def format_error(self, exc: BaseException) -> str:
        return f"{type(exc).__name__}: {exc}"

    def should_continue(self, exc: BaseException) -> bool:
        return self.classify(exc) != "fatal"

    def ready(self) -> bool:
        return True

    def dump(self) -> dict:
        return {"name": type(self).__name__, "version": self.VERSION,
                "recoverable": [t.__name__ for t in self.RECOVERABLE],
                "fatal": [t.__name__ for t in self.FATAL]}


__all__ = ["WSExceptionPolicy"]
