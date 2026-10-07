"""草稿存储。职责：待审核块 JSONL 读写（每 job 一文件）。
不做检索（preview 管）、不入库（commit 管）。
路径：~/.cache/agent_knowledge/drafts/<job_id>.jsonl（项目外）。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

import json
import os
from pathlib import Path
from threading import RLock
from typing import Optional, Sequence

from backend.rag.ingest.jobs.review_contracts import DraftChunk

DEFAULT_ROOT = os.path.expanduser("~/.cache/agent_knowledge/drafts")


class DraftStore:
    def __init__(self, root: Optional[str] = None) -> None:
        self._root = Path(root or DEFAULT_ROOT)
        self._lock = RLock()

    @property
    def root(self) -> str:
        return str(self._root)

    def _path(self, job_id: str) -> Path:
        if not job_id: raise ValueError("job_id required")
        return self._root / f"{job_id}.jsonl"

    def write(self, job_id: str, chunks: Sequence[DraftChunk]) -> str:
        """整批写入。原子：临时文件 → replace。返回草稿路径。"""
        self._root.mkdir(parents=True, exist_ok=True)
        p = self._path(job_id)
        tmp = p.with_suffix(".jsonl.tmp")
        with self._lock:
            with tmp.open("w", encoding="utf-8") as f:
                for c in chunks:
                    f.write(json.dumps(c.to_dict(), ensure_ascii=False))
                    f.write("\n")
            tmp.replace(p)
        return str(p)

    def read(self, job_id: str) -> list:
        p = self._path(job_id)
        if not p.exists():
            return []
        out: list = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    d = json.loads(line)
                    out.append(DraftChunk.from_dict(d))
                except Exception:
                    continue
        return out

    def count(self, job_id: str) -> int:
        p = self._path(job_id)
        if not p.exists(): return 0
        n = 0
        with p.open("r", encoding="utf-8") as f:
            for _ in f: n += 1
        return n

    def exists(self, job_id: str) -> bool:
        return self._path(job_id).exists()

    def delete(self, job_id: str) -> bool:
        try:
            p = self._path(job_id)
            if p.exists():
                p.unlink()
                return True
        except Exception as e:
            swallow("rag.ingest.jobs.draft_store:79", e)
        return False


_DEFAULT: Optional[DraftStore] = None


def get_default_draft_store() -> DraftStore:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = DraftStore()
    return _DEFAULT


def set_default_draft_store(s: Optional[DraftStore]) -> None:
    global _DEFAULT
    _DEFAULT = s


__all__ = ["DraftStore", "get_default_draft_store",
           "set_default_draft_store", "DEFAULT_ROOT"]
