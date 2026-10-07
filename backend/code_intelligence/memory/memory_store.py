from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from backend.code_intelligence.memory.similarity import jaccard
from backend.code_intelligence.memory.memory_store_index import (
    create_index_schema,
    index_load,
    index_upsert_many,
)


class MemoryStore:
    """项目级持久化记忆（rules + patches + code_index）。"""

    VERSION = "1.1"
    _LOCK = threading.Lock()
    _CACHE: dict[str, "MemoryStore"] = {}

    def __init__(self, workspace: str) -> None:
        self.workspace = str(Path(workspace).expanduser().resolve())
        digest = hashlib.sha1(
            self.workspace.encode("utf-8")
        ).hexdigest()[:16]
        root = Path.home() / ".biancheng" / "projects" / digest
        root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "memory.db"
        self._init_schema()

    @classmethod
    def for_workspace(cls, workspace: str) -> "MemoryStore":
        key = str(Path(workspace).expanduser().resolve())
        with cls._LOCK:
            store = cls._CACHE.get(key)
            if store is None:
                store = cls(key)
                cls._CACHE[key] = store
            return store

    def _init_schema(self) -> None:
        from backend.code_intelligence.memory._shared.schema import (
            init_rules_patches,
        )
        from backend.code_intelligence.memory.memory_store_index import (
            create_index_schema,
        )
        with sqlite3.connect(self.db_path) as conn:
            init_rules_patches(conn)
            create_index_schema(conn)

    def add_rule(self, rule: str, source: str = "user") -> int:
        rule = (rule or "").strip()
        if not rule:
            raise ValueError("rule required")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO rules(workspace, rule, source, created_at) "
                "VALUES(?, ?, ?, ?)",
                (self.workspace, rule, source, time.time()),
            )
            return int(cur.lastrowid)

    def list_rules(self, limit: int = 50) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, rule, source, created_at FROM rules "
                "WHERE workspace=? ORDER BY id DESC LIMIT ?",
                (self.workspace, limit),
            ).fetchall()
        return [
            {"id": r[0], "rule": r[1], "source": r[2], "created_at": r[3]}
            for r in rows
        ]

    # ─── patches ──────────────────────────────────
    def record_patch(
        self, *, task: str, plan: str, kind: str, text: str,
        accepted: bool, attempts: int = 1,
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO patches("
                "workspace, task, plan, kind, text, "
                "accepted, attempts, created_at) "
                "VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (self.workspace, task, plan or "", kind, text,
                 1 if accepted else 0, attempts, time.time()),
            )
            return int(cur.lastrowid)

    def find_similar_accepted(
        self, task: str, limit: int = 3, min_score: float = 0.25,
    ) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT task, plan, kind, text, attempts "
                "FROM patches WHERE workspace=? AND accepted=1 "
                "ORDER BY id DESC LIMIT 200",
                (self.workspace,),
            ).fetchall()
        scored = []
        for r in rows:
            s = jaccard(task, r[0])
            if s >= min_score:
                scored.append((s, {
                    "task": r[0], "plan": r[1], "kind": r[2],
                    "text": r[3], "attempts": r[4], "score": s,
                }))
        scored.sort(key=lambda x: -x[0])
        return [item for _, item in scored[:limit]]

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            rules = conn.execute(
                "SELECT COUNT(*) FROM rules WHERE workspace=?",
                (self.workspace,),
            ).fetchone()[0]
            patches = conn.execute(
                "SELECT COUNT(*) FROM patches WHERE workspace=?",
                (self.workspace,),
            ).fetchone()[0]
            accepted = conn.execute(
                "SELECT COUNT(*) FROM patches "
                "WHERE workspace=? AND accepted=1",
                (self.workspace,),
            ).fetchone()[0]
            idx = conn.execute(
                "SELECT COUNT(*) FROM code_index WHERE workspace=?",
                (self.workspace,),
            ).fetchone()[0]
        return {"workspace": self.workspace, "db_path": str(self.db_path),
                "rules": rules, "patches": patches,
                "accepted_patches": accepted, "index_entries": idx}

    # ─── code_index（委托 memory_store_index） ─────
    def index_load(self) -> dict[str, dict[str, Any]]:
        return index_load(self.db_path, self.workspace)

    def index_upsert_many(self, entries: list[dict[str, Any]]) -> int:
        return index_upsert_many(self.db_path, self.workspace, entries)

    def ready(self) -> bool:
        return self.db_path.exists()

    def dump(self) -> dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "workspace": self.workspace, "db_path": str(self.db_path),
                "stats": self.stats()}


__all__ = ["MemoryStore"]
