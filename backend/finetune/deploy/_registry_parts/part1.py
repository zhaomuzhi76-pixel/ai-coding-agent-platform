"""Part 1 of registry.py."""
from __future__ import annotations

import json

import sqlite3

import time

from pathlib import Path

from typing import Any

from ..spec import (
    AdapterSpec, AdapterMethod, AdapterTarget, MergeMode,
    create_adapter_spec,
)

_DB_DIR = Path.home() / ".biancheng"

_DB_PATH = _DB_DIR / "metrics.db"

_FINETUNE_DIR = _DB_DIR / "finetune"

def _ensure_schema() -> None:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_DB_PATH) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS finetune_adapters (
                adapter_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_model TEXT NOT NULL,
                adapter_path TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'lora',
                target TEXT NOT NULL DEFAULT 'ollama',
                merge_mode TEXT NOT NULL DEFAULT 'adapter_only',
                ollama_model_name TEXT NOT NULL DEFAULT '',
                source_job_id TEXT NOT NULL DEFAULT '',
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                tags_json TEXT NOT NULL DEFAULT '[]'
            );
            CREATE INDEX IF NOT EXISTS idx_ft_adapters_created
                ON finetune_adapters(created_at DESC);
        """)

def save_adapter_spec(spec: AdapterSpec) -> None:
    if not isinstance(spec, AdapterSpec):
        raise TypeError("spec must AdapterSpec")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO finetune_adapters("
            "adapter_id, name, base_model, adapter_path, method, target, "
            "merge_mode, ollama_model_name, source_job_id, size_bytes, "
            "created_at, description, tags_json) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                spec.adapter_id, spec.name, spec.base_model, spec.adapter_path,
                spec.method.value, spec.target.value, spec.merge_mode.value,
                spec.ollama_model_name, spec.source_job_id,
                int(spec.size_bytes), float(spec.created_at),
                spec.description,
                json.dumps(list(spec.tags), ensure_ascii=False),
            ),
        )

def load_adapter_spec(adapter_id: str) -> AdapterSpec | None:
    if not adapter_id or not adapter_id.strip():
        raise ValueError("adapter_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        row = conn.execute(
            "SELECT adapter_id, name, base_model, adapter_path, method, target, "
            "merge_mode, ollama_model_name, source_job_id, size_bytes, "
            "created_at, description, tags_json "
            "FROM finetune_adapters WHERE adapter_id = ?",
            (adapter_id.strip(),),
        ).fetchone()
    if row is None:
        return None
    try: method = AdapterMethod(row[4])
    except ValueError: method = AdapterMethod.LORA
    try: target = AdapterTarget(row[5])
    except ValueError: target = AdapterTarget.OLLAMA
    try: merge_mode = MergeMode(row[6])
    except ValueError: merge_mode = MergeMode.ADAPTER_ONLY
    return AdapterSpec(
        adapter_id=row[0], name=row[1], base_model=row[2],
        adapter_path=row[3], method=method, target=target,
        merge_mode=merge_mode, ollama_model_name=row[7],
        source_job_id=row[8], size_bytes=int(row[9]),
        created_at=float(row[10]), description=row[11],
        tags=tuple(str(t) for t in json.loads(row[12] or "[]")),
    )

def list_adapter_specs(limit: int = 100) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT adapter_id, name, base_model, adapter_path, method, target, "
            "merge_mode, ollama_model_name, source_job_id, size_bytes, "
            "created_at, description, tags_json "
            "FROM finetune_adapters "
            "ORDER BY created_at DESC, rowid DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append({
            "adapter_id": row[0], "name": row[1], "base_model": row[2],
            "adapter_path": row[3], "method": row[4], "target": row[5],
            "merge_mode": row[6], "ollama_model_name": row[7],
            "source_job_id": row[8], "size_bytes": int(row[9]),
            "created_at": float(row[10]), "description": row[11],
            "tags": list(json.loads(row[12] or "[]")),
        })
    return out

def delete_adapter_spec(adapter_id: str) -> bool:
    if not adapter_id or not adapter_id.strip():
        raise ValueError("adapter_id required")
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        cur = conn.execute(
            "DELETE FROM finetune_adapters WHERE adapter_id = ?",
            (adapter_id.strip(),),
        )
        return cur.rowcount > 0

def reset_adapter_specs() -> None:
    _ensure_schema()
    with sqlite3.connect(_DB_PATH) as conn:
        conn.execute("DELETE FROM finetune_adapters")

def _dir_size_bytes(p: Path) -> int:
    if not p.exists():
        return 0
    total = 0
    try:
        for f in p.rglob("*"):
            if f.is_file():
                try: total += f.stat().st_size
                except OSError: pass
    except OSError:
        pass
    return total
