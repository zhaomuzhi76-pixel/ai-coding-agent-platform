"""精确类名匹配器（单一职责）。

从 desc.db 加载全部 class_name，query 里最长子串匹配。
命中 → 直接 SQLite 查图（零推理延迟）。
不命中 → 返回空，让上层兜底走 CLIP 语义检索。
"""
from __future__ import annotations
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


def _to_url(image_path: str) -> str:
    try:
        from backend.rag.retrieval_paths import _to_url as tu
        return tu(image_path)
    except Exception:
        return image_path or ""


_ALIAS = {
    # 用户说法 → desc.db 真实类名（双向兜底）
    "芍药": ["白芍", "赤芍", "川赤芍", "芍药"],
    "白芍": ["芍药", "白芍"],
    "赤芍": ["芍药", "赤芍"],
    "川赤芍": ["芍药", "川赤芍"],
    "人参": ["人参"],
    "黄芪": ["黄芪", "黄耆", "膜荚黄芪"],
    "黄耆": ["黄芪", "黄耆"],
    "银花": ["金银花", "银花"],
    "金银花": ["金银花"],
    "神草": ["人参"],
    "地黄": ["地黄", "生地", "熟地"],
    "生地": ["地黄"],
    "熟地": ["地黄"],
}


class ExactClassMatcher:
    """SQLite class_name 精确匹配器（单例缓存）。"""

    def __init__(self, db_path: str = "vector_db/lite_image_desc.db",
                 cache_ttl: int = 600) -> None:
        self._db = db_path
        self._classes: Optional[List[str]] = None
        self._loaded_at: float = 0.0
        self._ttl = cache_ttl

    def _ensure_loaded(self) -> None:
        import time as _t
        now = _t.time()
        if self._classes is not None and (now - self._loaded_at) < self._ttl:
            return
        if not os.path.exists(self._db):
            self._classes = []
            return
        try:
            conn = sqlite3.connect(self._db)
            c = conn.cursor()
            c.execute(
                "SELECT DISTINCT json_extract(metadata, '$.class_name') "
                "FROM docs WHERE json_extract(metadata, '$.class_name') "
                "IS NOT NULL")
            rows = c.fetchall()
            conn.close()
            self._classes = sorted(
                [str(r[0]) for r in rows if r[0]],
                key=len, reverse=True)
            self._loaded_at = now
        except Exception:
            self._classes = []

    def extract_class(self, query: str) -> Optional[str]:
        """从 query 提取最长匹配的 class_name（含别名解析）。"""
        if not query:
            return None
        self._ensure_loaded()
        # 路径 1：直接命中 desc.db 类名
        for cn in (self._classes or ()):
            if cn in query:
                return cn
        # 路径 2：别名 → 反查 desc.db
        for alias, cands in _ALIAS.items():
            if alias in query:
                for c in cands:
                    if c in (self._classes or ()):
                        return c
        return None

    def search(self, query: str, *, limit: int = 5) -> List[Dict[str, Any]]:
        """精确匹配 → 返回图片列表（未命中返回 []）。"""
        cls = self.extract_class(query)
        if not cls:
            return []
        try:
            conn = sqlite3.connect(self._db)
            c = conn.cursor()
            c.execute(
                "SELECT id, text, metadata FROM docs "
                "WHERE json_extract(metadata, '$.class_name') = ? "
                "LIMIT ?", (cls, int(limit)))
            rows = c.fetchall()
            conn.close()
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        for rid, text, mj in rows:
            try:
                m = json.loads(mj) if isinstance(mj, str) else (mj or {})
            except Exception:
                m = {}
            ip = m.get("image_path", "") or ""
            url = _to_url(ip) if ip else ""
            if not url:
                continue
            out.append({
                "id": rid,
                "url": url,
                "class_name": cls,
                "alt_text": str(text or cls)[:100],
                "score": 1.0,
            })
        return out

    def count_classes(self) -> int:
        self._ensure_loaded()
        return len(self._classes or [])


_GLOBAL: Optional[ExactClassMatcher] = None


def get_default_matcher() -> ExactClassMatcher:
    global _GLOBAL
    if _GLOBAL is None:
        _GLOBAL = ExactClassMatcher()
    return _GLOBAL


__all__ = ["ExactClassMatcher", "get_default_matcher"]
