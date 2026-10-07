"""GPU 锁看门狗。职责：自动过期残留锁 + 启动时清理。
不实现锁获取（gpu_lock 管）、不改 holder 协议。
环境变量：
  RAG_GPU_LOCK_TTL=600  秒（默认 10 分钟）
"""
from __future__ import annotations
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
_DEFAULT_TTL = int(os.environ.get("RAG_GPU_LOCK_TTL", "600"))


def _lock_path() -> Path:
    base = os.environ.get(
        "RAG_GPU_LOCK_DIR",
        os.path.expanduser("~/.cache/agent_knowledge"))
    return Path(base) / "gpu.lock"


def _read() -> Optional[dict]:
    p = _lock_path()
    if not p.is_file():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def clean_stale(ttl: Optional[int] = None) -> bool:
    """若 holder 存在且 ts 早于 ttl 秒前，视为残留并清空。
    返回 True 表示清理了一个残留锁。"""
    ttl = _DEFAULT_TTL if ttl is None else ttl
    d = _read()
    if not d:
        return False
    holder = d.get("holder") or ""
    ts = float(d.get("ts") or 0)
    if not holder:
        return False
    age = time.time() - ts
    if age > ttl:
        try:
            _lock_path().unlink()
            logger.warning(
                "[gpu-lock-wd] 清残留锁 holder=%s age=%.0fs > %ds",
                holder, age, ttl)
            return True
        except OSError:
            pass
    return False


def status() -> dict:
    d = _read() or {}
    return {
        "holder": d.get("holder", ""),
        "need_mb": int(d.get("need_mb", 0) or 0),
        "age_s": int(time.time() - float(d.get("ts", 0) or 0))
        if d.get("ts") else 0,
        "ttl_s": _DEFAULT_TTL,
    }


__all__ = ["clean_stale", "status", "_DEFAULT_TTL"]
