"""L2 · Message Bus（进程内 Agent 间通信）。

职责：
  · publish(msg) / subscribe(topic, fn)
  · emit_to_agent(aid, topic, payload)
  · drain(agent_id) / peek(agent_id)
  · recent(n) / stats()
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from threading import RLock
from typing import Any, Callable, Dict, Deque, List, Optional


@dataclass(frozen=True)
class Message:
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    sender: str = ""
    receiver: str = ""
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MessageBus:
    def __init__(self, maxlen: int = 2000) -> None:
        self._subs: Dict[str, List[Callable[[Message], None]]] = {}
        self._inbox: Dict[str, Deque[Message]] = {}
        self._history: Deque[Message] = deque(maxlen=maxlen)
        self._lock = RLock()

    def subscribe(self, topic: str,
                  handler: Callable[[Message], None]) -> None:
        with self._lock:
            self._subs.setdefault(topic, []).append(handler)

    def unsubscribe(self, topic: str,
                    handler: Callable[[Message], None]) -> bool:
        with self._lock:
            lst = self._subs.get(topic, [])
            if handler in lst:
                lst.remove(handler); return True
            return False

    def publish(self, msg: Message) -> int:
        if not isinstance(msg, Message):
            raise TypeError("msg must be Message")
        with self._lock:
            self._history.append(msg)
            if msg.receiver:
                self._inbox.setdefault(
                    msg.receiver, deque(maxlen=500)).append(msg)
            handlers = list(self._subs.get(msg.topic, []))
        for h in handlers:
            try:
                h(msg)
            except Exception:
                pass
        return len(handlers)

    def emit_to_agent(self, agent_id: str, topic: str,
                      payload: Dict[str, Any], sender: str = "") -> Message:
        msg = Message(topic=topic, payload=payload,
                      sender=sender, receiver=agent_id)
        self.publish(msg)
        return msg

    def drain(self, agent_id: str) -> List[Message]:
        with self._lock:
            dq = self._inbox.get(agent_id)
            if not dq:
                return []
            out = list(dq); dq.clear(); return out

    def peek(self, agent_id: str) -> List[Message]:
        with self._lock:
            return list(self._inbox.get(agent_id) or ())

    def recent(self, n: int = 20) -> List[Message]:
        with self._lock:
            return list(self._history)[-n:]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "topics": list(self._subs.keys()),
                "subscribers": sum(len(v) for v in self._subs.values()),
                "history": len(self._history),
                "inboxes": {k: len(v) for k, v in self._inbox.items()},
            }

    def clear(self) -> None:
        with self._lock:
            self._subs.clear(); self._inbox.clear(); self._history.clear()


_DEFAULT: Optional[MessageBus] = None


def get_default_bus() -> MessageBus:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = MessageBus()
    return _DEFAULT


__all__ = ["MessageBus", "Message", "get_default_bus"]
