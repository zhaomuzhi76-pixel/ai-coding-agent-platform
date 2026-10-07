"""会话历史存储。职责：按 session_id 存/取消息列表。
不调 LLM、不执行工具、不做裁剪策略（交给 chat_loop）。
线程安全，内存实现；持久化可后续接 backend/persistence。"""
from __future__ import annotations
from threading import RLock
from typing import Any, Mapping, Optional

MAX_MESSAGES_PER_SESSION = 200
MAX_SESSIONS = 1000

class SessionHistory:
    def __init__(self, *, max_messages: int = MAX_MESSAGES_PER_SESSION,
                 max_sessions: int = MAX_SESSIONS) -> None:
        if max_messages <= 0 or max_sessions <= 0:
            raise ValueError("max_messages / max_sessions must be > 0")
        self._data: dict[str, list[dict]] = {}
        self._order: list[str] = []
        self._lock = RLock()
        self._max_msg = max_messages
        self._max_sess = max_sessions

    def append_user(self, sid: str, text: str) -> None:
        self._append(sid, {"role": "user", "content": str(text)})

    def append_assistant(self, sid: str, text: str,
                         meta: Optional[Mapping[str, Any]] = None) -> None:
        msg: dict[str, Any] = {"role": "assistant", "content": str(text)}
        if meta:
            msg["meta"] = dict(meta)
        self._append(sid, msg)

    def messages(self, sid: str) -> list[dict]:
        with self._lock:
            return [dict(m) for m in self._data.get(sid, [])]

    def reset(self, sid: str) -> None:
        with self._lock:
            self._data.pop(sid, None)
            if sid in self._order:
                self._order.remove(sid)
        # [PERSIST] 同步清磁盘
        try:
            from backend.agent_tools.session_persist import get_default_persist
            get_default_persist().drop(sid)
        except Exception:
            pass

    def drop(self, sid: str) -> None:
        self.reset(sid)

    def sessions(self) -> list[str]:
        with self._lock:
            return list(self._order)

    def message_count(self, sid: str) -> int:
        with self._lock:
            return len(self._data.get(sid, []))

    def _append(self, sid: str, msg: dict) -> None:
        if not sid:
            raise ValueError("session_id required")
        with self._lock:
            if sid not in self._data:
                self._order.append(sid)
                if len(self._order) > self._max_sess:
                    old = self._order.pop(0)
                    self._data.pop(old, None)
                # [PERSIST] 首次：从磁盘恢复历史
                try:
                    from backend.agent_tools.session_persist import (
                        get_default_persist)
                    self._data[sid] = list(get_default_persist().load(sid))
                except Exception:
                    self._data[sid] = []
            bucket = self._data[sid]
            bucket.append(msg)
            if len(bucket) > self._max_msg:
                del bucket[:len(bucket) - self._max_msg]
        # [PERSIST] 落盘（锁外，异常静默）
        try:
            from backend.agent_tools.session_persist import (
                get_default_persist)
            get_default_persist().append(sid, msg)
        except Exception:
            pass

_DEFAULT: Optional[SessionHistory] = None
def get_default_history() -> SessionHistory:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = SessionHistory()
    return _DEFAULT

__all__ = ["SessionHistory", "get_default_history"]
