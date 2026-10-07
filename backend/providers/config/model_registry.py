"""模型注册表：只有"用户验证通过"的模型才进前端下拉。

工业级契约：
    - metrics.db 加 model_registry 表（共享库，与 cost/audit 同）
    - 首次启动自动导入 catalog 全量模型，**排除微调产物**（finetune_adapters）
    - 前端 /api/platform/models 只返回 verified=1 的模型
    - 用户通过配置中心 [验证] / [取消验证] 管理

不负责：
    - 发现模型（ollama_discovery 管）
    - 构造 catalog（registry_builder 管）
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"


def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS model_registry (
                model_name TEXT PRIMARY KEY,
                verified INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'manual',
                verified_at REAL NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_model_registry_verified
                ON model_registry(verified, model_name);
        """)


def _finetune_model_names() -> set:
    """从 finetune_adapters 表读取微调产物的 ollama_model_name。"""
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT ollama_model_name FROM finetune_adapters "
                "WHERE ollama_model_name != ''"
            ).fetchall()
            return {str(r[0]) for r in rows if r[0]}
    except Exception:
        return set()


def is_verified(model_name: str) -> bool:
    if not model_name:
        return False
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            row = conn.execute(
                "SELECT verified FROM model_registry WHERE model_name=?",
                (model_name,),
            ).fetchone()
            return bool(row and row[0])
    except Exception:
        return False


def list_verified() -> list[str]:
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT model_name FROM model_registry "
                "WHERE verified=1 ORDER BY model_name"
            ).fetchall()
            return [r[0] for r in rows]
    except Exception:
        return []


def list_all() -> list[dict]:
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM model_registry ORDER BY model_name"
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def verify(model_name: str, source: str = "manual") -> bool:
    if not model_name or not model_name.strip():
        return False
    name = model_name.strip()
    _ensure_schema()
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            now = time.time()
            conn.execute(
                "INSERT INTO model_registry("
                "model_name, verified, source, verified_at, created_at) "
                "VALUES(?, 1, ?, ?, ?) "
                "ON CONFLICT(model_name) DO UPDATE SET "
                "verified=1, source=excluded.source, verified_at=excluded.verified_at",
                (name, source, now, now),
            )
            return True
    except Exception:
        return False


def unverify(model_name: str) -> bool:
    if not model_name or not model_name.strip():
        return False
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                "UPDATE model_registry SET verified=0, verified_at=0 "
                "WHERE model_name=?",
                (model_name.strip(),),
            )
            return True
    except Exception:
        return False


def maybe_bootstrap(all_model_names: list[str]) -> int:
    """首次启动：把 catalog 里所有模型登记为 verified=1，**排除微调产物**。

    幂等：一旦 model_registry 表有记录，不再执行。
    """
    _ensure_schema()
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM model_registry"
            ).fetchone()[0]
            if count > 0:
                return 0
    except Exception:
        return 0

    ft_names = _finetune_model_names()
    to_register = [m for m in all_model_names if m and m not in ft_names]
    now = time.time()
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            for name in to_register:
                conn.execute(
                    "INSERT OR IGNORE INTO model_registry("
                    "model_name, verified, source, verified_at, created_at) "
                    "VALUES(?, 1, 'bootstrap', ?, ?)",
                    (name, now, now),
                )
            # 微调产物显式登记为未验证（供管理面板展示）
            for name in ft_names:
                conn.execute(
                    "INSERT OR IGNORE INTO model_registry("
                    "model_name, verified, source, verified_at, created_at) "
                    "VALUES(?, 0, 'finetune', 0, ?)",
                    (name, now),
                )
        return len(to_register)
    except Exception:
        return 0


__all__ = [
    "is_verified", "list_verified", "list_all",
    "verify", "unverify", "maybe_bootstrap",
]
