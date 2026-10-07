from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from backend.code_intelligence.memory.similarity import jaccard


class SkillLibrary:
    """
    跨项目技能库（肌肉记忆）。

    一次成功的操作模式（如"给函数加日志"）被反复使用后，
    变成"肌肉记忆"，直接复用不用重新推理。

    存储：~/.biancheng/global/global.db:skills
    """

    VERSION = "1.0"
    _LOCK = threading.Lock()
    _INSTANCE: "SkillLibrary | None" = None

    def __init__(self) -> None:
        root = Path.home() / ".biancheng" / "global"
        root.mkdir(parents=True, exist_ok=True)
        self.db_path = root / "global.db"
        self._init_schema()

    @classmethod
    def instance(cls) -> "SkillLibrary":
        with cls._LOCK:
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE

    def _init_schema(self) -> None:
        from backend.code_intelligence.memory._shared.schema import (
            init_skills,
        )
        with sqlite3.connect(self.db_path) as conn:
            init_skills(conn)

    @staticmethod
    def _signature(task: str) -> str:
        """归一化任务签名。"""
        return hashlib.sha1(
            " ".join(sorted(task.lower().split()))
            .encode("utf-8")
        ).hexdigest()[:16]

    def record(
        self,
        *,
        task: str,
        plan: str,
        kind: str,
        text: str,
        workspace: str,
    ) -> None:
        """记录一次成功执行。"""
        sig = self._signature(task)
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, success_count FROM skills "
                "WHERE signature=?", (sig,)
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE skills SET "
                    "success_count=success_count+1, "
                    "last_used_at=? WHERE id=?",
                    (now, row[0]),
                )
            else:
                conn.execute(
                    "INSERT INTO skills("
                    "signature, task_pattern, plan_template, "
                    "kind, text_template, success_count, "
                    "project_count, last_used_at, created_at) "
                    "VALUES(?, ?, ?, ?, ?, 1, 1, ?, ?)",
                    (sig, task, plan, kind, text, now, now),
                )

    def lookup(
        self,
        task: str,
        min_score: float = 0.5,
        min_success: int = 2,
    ) -> dict[str, Any] | None:
        """查是否有可复用的技能。"""
        # 精确签名
        sig = self._signature(task)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT task_pattern, plan_template, kind, "
                "text_template, success_count FROM skills "
                "WHERE signature=? AND success_count>=?",
                (sig, min_success),
            ).fetchone()
            if row:
                return {
                    "task": row[0], "plan": row[1],
                    "kind": row[2], "text": row[3],
                    "success_count": row[4], "match": "exact",
                }

            # 相似匹配
            rows = conn.execute(
                "SELECT task_pattern, plan_template, kind, "
                "text_template, success_count FROM skills "
                "WHERE success_count>=? ORDER BY success_count DESC LIMIT 50",
                (min_success,),
            ).fetchall()

        best = None
        best_score = min_score
        for r in rows:
            score = jaccard(task, r[0])
            if score > best_score:
                best_score = score
                best = {
                    "task": r[0], "plan": r[1],
                    "kind": r[2], "text": r[3],
                    "success_count": r[4],
                    "match": "similar", "score": score,
                }
        return best

    def stats(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            n = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
            top = conn.execute(
                "SELECT task_pattern, success_count FROM skills "
                "ORDER BY success_count DESC LIMIT 5"
            ).fetchall()
        return {
            "total_skills": n,
            "top": [{"task": r[0], "uses": r[1]} for r in top],
        }


__all__ = ["SkillLibrary"]
