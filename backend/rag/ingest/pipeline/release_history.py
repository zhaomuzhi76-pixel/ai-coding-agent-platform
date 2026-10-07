"""Pipeline 释放历史（SQLite，可追溯）。
DB 路径：~/.cache/agent_knowledge/idle_history.db
保留天数优先级：env RAG_IDLE_HISTORY_DAYS > rag_config.json > 60
每次 purge 动态读取，改配置立即生效（无需重启）。
"""
from __future__ import annotations
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_RAG_CFG = os.path.expanduser("~/.biancheng/rag_config.json")


def _default_db_path() -> str:
    override = os.environ.get("RAG_IDLE_DB_PATH", "")
    if override:
        return override
    base = os.path.expanduser("~/.cache/agent_knowledge")
    Path(base).mkdir(parents=True, exist_ok=True)
    return os.path.join(base, "idle_history.db")


def _read_config_file_days() -> Optional[int]:
    """从 rag_config.json 读 idle_history_days。失败返回 None。"""
    if not os.path.isfile(_RAG_CFG):
        return None
    try:
        with open(_RAG_CFG, "r", encoding="utf-8") as f:
            d = json.load(f)
        v = d.get("idle_history_days")
        if v is None:
            return None
        n = int(v)
        return n if n > 0 else None
    except Exception:
        return None


def _resolve_history_days() -> int:
    """env > rag_config.json > 60。"""
    raw = os.environ.get("RAG_IDLE_HISTORY_DAYS")
    if raw is not None and str(raw).strip():
        try:
            n = int(str(raw).strip())
            if n > 0:
                return n
        except (TypeError, ValueError):
            pass
    cfg = _read_config_file_days()
    if cfg is not None:
        return cfg
    return 60


def _gpu_used(d: dict) -> int:
    return int((d.get("gpu") or {}).get("used_mb", 0) or 0)


def _cpu_pct(d: dict) -> float:
    return float((d.get("cpu") or {}).get("percent", 0.0) or 0.0)


def _mem_pct(d: dict) -> float:
    return float((d.get("mem") or {}).get("percent", 0.0) or 0.0)


class ReleaseHistory:
    """SQLite 持久化释放历史。线程安全。"""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _default_db_path()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                reasons TEXT DEFAULT '',
                freed TEXT DEFAULT '',
                delta_vram_mb INTEGER DEFAULT 0,
                delta_cpu_pct REAL DEFAULT 0,
                delta_mem_pct REAL DEFAULT 0,
                before_json TEXT DEFAULT '{}',
                after_json TEXT DEFAULT '{}',
                trigger TEXT DEFAULT 'auto'
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ts ON releases(ts DESC)")
        self._conn.commit()
        self._lock = threading.Lock()

    @property
    def db_path(self) -> str:
        return self._db_path

    def record(self, info: dict, *, trigger: str = "auto") -> int:
        before = info.get("before") or {}
        after = info.get("after") or {}
        # [CLAMP] 释放量不能为负（前后探测可能波动）
        d_vram = max(0, _gpu_used(before) - _gpu_used(after))
        d_cpu = max(0.0, round(_cpu_pct(before) - _cpu_pct(after), 2))
        d_mem = max(0.0, round(_mem_pct(before) - _mem_pct(after), 2))
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO releases "
                "(ts, reasons, freed, delta_vram_mb, delta_cpu_pct, "
                " delta_mem_pct, before_json, after_json, trigger) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (float(info.get("ts") or time.time()),
                 json.dumps(info.get("reasons") or [], ensure_ascii=False),
                 json.dumps(info.get("freed") or [], ensure_ascii=False),
                 d_vram, d_cpu, d_mem,
                 json.dumps(before, ensure_ascii=False),
                 json.dumps(after, ensure_ascii=False),
                 trigger))
            self._conn.commit()
            return int(cur.lastrowid or 0)

    def list_recent(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        since = time.time() - hours * 3600
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, ts, reasons, freed, delta_vram_mb, "
                "delta_cpu_pct, delta_mem_pct, trigger "
                "FROM releases WHERE ts >= ? ORDER BY ts DESC LIMIT ?",
                (since, int(limit))).fetchall()
        return [{
            "id": r[0], "ts": r[1],
            "reasons": json.loads(r[2] or "[]"),
            "freed": json.loads(r[3] or "[]"),
            "delta_vram_mb": r[4], "delta_cpu_pct": r[5],
            "delta_mem_pct": r[6], "trigger": r[7],
        } for r in rows]

    def stats(self, hours: int = 24) -> Dict[str, Any]:
        since = time.time() - hours * 3600
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(delta_vram_mb),0), "
                "COALESCE(MAX(ts),0) FROM releases WHERE ts >= ?",
                (since,)).fetchone()
        return {"hours": int(hours), "count": int(row[0] or 0),
                "total_vram_freed_mb": int(row[1] or 0),
                "last_ts": float(row[2] or 0)}

    def purge_old(self, days: Optional[int] = None) -> int:
        d = int(days if days is not None else _resolve_history_days())
        cutoff = time.time() - d * 86400
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM releases WHERE ts < ?", (cutoff,))
            self._conn.commit()
            return int(cur.rowcount or 0)

    def retention_days(self) -> int:
        return _resolve_history_days()

    def close(self) -> None:
        try: self._conn.close()
        except Exception: pass


_singleton: Optional[ReleaseHistory] = None
_guard = threading.Lock()


def get_history() -> ReleaseHistory:
    global _singleton
    if _singleton is None:
        with _guard:
            if _singleton is None:
                _singleton = ReleaseHistory()
    return _singleton


__all__ = ["ReleaseHistory", "get_history",
           "_resolve_history_days", "_read_config_file_days",
           "_default_db_path"]
