"""会话历史落盘（JSONL）。

职责：
  - 把 SessionHistory 的 messages 存磁盘（跨进程/重启恢复）
  - 提供 append / load / drop / save_all
不做：
  - 不做裁剪策略（session.py 管）
  - 不调 LLM、不执行工具

存储：~/.cache/agent_knowledge/sessions/<sid>.jsonl
"""
from __future__ import annotations
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DIR = os.environ.get(
    "RAG_SESSION_DIR",
    os.path.expanduser("~/.cache/agent_knowledge/sessions"))
_MAX_LINES = int(os.environ.get("RAG_SESSION_MAX_LINES", "500"))


class SessionPersist:
    def __init__(self, dirpath: str = _DIR) -> None:
        self._dir = Path(dirpath)
        self._lock = threading.RLock()
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def path(self, sid: str) -> Path:
        safe = "".join(c for c in sid if c.isalnum() or c in "-_")
        safe = safe[:64] or "anon"
        return self._dir / f"{safe}.jsonl"

    def append(self, sid: str, msg: Dict[str, Any]) -> None:
        if not sid or not isinstance(msg, dict):
            return
        with self._lock:
            try:
                with open(self.path(sid), "a", encoding="utf-8") as f:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.debug("[persist] append %s: %r", sid, e)

    def load(self, sid: str, limit: int = 200) -> List[Dict[str, Any]]:
        p = self.path(sid)
        if not p.exists():
            return []
        try:
            with self._lock:
                out: List[Dict[str, Any]] = []
                with open(p, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            out.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return out[-limit:]
        except Exception as e:
            logger.debug("[persist] load %s: %r", sid, e)
            return []

    def drop(self, sid: str) -> None:
        with self._lock:
            p = self.path(sid)
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

    def save_all(self, sid: str, msgs: List[Dict[str, Any]]) -> None:
        """全量覆盖（用于裁剪对齐）。"""
        with self._lock:
            try:
                with open(self.path(sid), "w", encoding="utf-8") as f:
                    for m in msgs[-_MAX_LINES:]:
                        f.write(json.dumps(m, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.debug("[persist] save_all %s: %r", sid, e)


_DEFAULT: Optional[SessionPersist] = None


def get_default_persist() -> SessionPersist:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = SessionPersist()
    return _DEFAULT


__all__ = ["SessionPersist", "get_default_persist"]
