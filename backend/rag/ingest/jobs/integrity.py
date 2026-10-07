"""工业级完整性门禁。三层校验：草稿/向量库/入库后。
原则：不全不入库、校验失败全清、以真实状态为准。
不修改任何现有文件，独立插件。
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ═══════════════ L1: 草稿完整性 ═══════════════
def verify_draft(draft_path: str) -> Dict[str, Any]:
    """检查 draft 文件：行数、唯一 id、必填字段。
    返回 {ok, n_lines, n_unique_ids, errors, ids, chunks}
    """
    r: Dict[str, Any] = {"ok": False, "n_lines": 0, "n_unique_ids": 0,
                         "errors": [], "ids": [], "chunks": []}
    p = Path(draft_path)
    if not p.is_file():
        r["errors"].append(f"draft 不存在: {draft_path}")
        return r

    chunks: List[dict] = []
    with p.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(json.loads(line))
            except Exception as e:
                r["errors"].append(f"行 {lineno} JSON 解析失败: {e}")

    n = len(chunks)
    r["n_lines"] = n
    r["chunks"] = chunks

    if n == 0:
        r["errors"].append("draft 为空")
        return r

    # chunk_id 必填 + 唯一
    ids = []
    missing_id = 0
    for i, c in enumerate(chunks):
        cid = None
        if isinstance(c, dict):
            for k in ("chunk_id", "id", "_id", "uid"):
                if c.get(k):
                    cid = str(c[k]); break
        if not cid:
            missing_id += 1
            cid = f"__auto__{i}"   # 占位（后面 _extract 会用同一算法）
        ids.append(cid)

    r["ids"] = ids
    r["n_unique_ids"] = len(set(ids))

    if missing_id > 0:
        r["errors"].append(f"{missing_id} 条无 chunk_id")
    if len(set(ids)) != n:
        r["errors"].append(f"chunk_id 重复: {n} 行 -> {len(set(ids))} 唯一")

    r["ok"] = len(r["errors"]) == 0
    return r


# ═══════════════ L2: 向量库状态反查 ═══════════════
def list_stored_ids(vs: Any, job_id: str) -> Set[str]:
    """从向量库反查该 job 已存储的所有 chunk_id。"""
    out: Set[str] = set()
    try:
        if not hasattr(vs, "_conn"):
            return out
        cur = vs._conn.execute("SELECT id, metadata FROM docs")
        for id_, meta_str in cur.fetchall():
            try:
                m = json.loads(meta_str or "{}")
            except Exception:
                continue
            if m.get("job_id") == job_id or m.get("_job_id") == job_id:
                out.add(str(id_))
    except Exception as e:
        logger.warning("[integrity] list_stored_ids 失败: %r", e)
    return out


def actual_offset(vs: Any, job_id: str, draft_ids: List[str]) -> int:
    """真实 offset = draft_ids 里第一个"不在向量库"的位置。
    以向量库为准，绕过被污染的内存 offset。
    """
    stored = list_stored_ids(vs, job_id)
    for i, did in enumerate(draft_ids):
        if did not in stored:
            return i
    return len(draft_ids)


def count_stored(vs: Any, job_id: str) -> int:
    """向量库里该 job 的 chunk 总数。"""
    return len(list_stored_ids(vs, job_id))


# ═══════════════ L3: 清理 + 回滚 ═══════════════
def clear_job_data(vs: Any, job_id: str) -> int:
    """删除向量库里该 job 的所有 chunk。返回删除数。"""
    n = 0
    try:
        if not hasattr(vs, "_conn"):
            return 0
        cur = vs._conn.execute("SELECT id, metadata FROM docs")
        for id_, meta_str in cur.fetchall():
            try:
                m = json.loads(meta_str or "{}")
            except Exception:
                continue
            if m.get("job_id") == job_id or m.get("_job_id") == job_id:
                vs._conn.execute("DELETE FROM docs WHERE id=?", (id_,))
                n += 1
        vs._conn.commit()
        vs._cache = None
    except Exception as e:
        logger.warning("[integrity] clear_job_data 失败: %r", e)
    return n


# ═══════════════ 主校验器 ═══════════════
def validate_before_ingest(draft_path: str, total_hint: int = 0
                            ) -> Tuple[bool, Dict[str, Any]]:
    """入库前校验：draft 必须完整。
    total_hint > 0 时，draft 行数必须 == total_hint（否则拒绝）。
    """
    r = verify_draft(draft_path)
    if not r["ok"]:
        return False, r
    if total_hint > 0 and r["n_lines"] != total_hint:
        r["errors"].append(
            f"draft 行数 {r['n_lines']} != 预期 {total_hint}")
        r["ok"] = False
        return False, r
    return True, r


def validate_after_ingest(vs: Any, job_id: str, expected_ids: List[str]
                          ) -> Tuple[bool, Dict[str, Any]]:
    """入库后校验：向量库该 job 的 chunk_id 集合必须 == draft 的集合。"""
    stored = list_stored_ids(vs, job_id)
    expected = set(expected_ids)
    missing = expected - stored
    extra = stored - expected
    r = {"ok": False, "n_stored": len(stored), "n_expected": len(expected),
         "n_missing": len(missing), "n_extra": len(extra),
         "missing_sample": list(missing)[:5],
         "extra_sample": list(extra)[:5]}
    if missing or extra:
        return False, r
    r["ok"] = True
    return True, r


__all__ = ["verify_draft", "validate_before_ingest",
           "validate_after_ingest", "list_stored_ids",
           "actual_offset", "count_stored", "clear_job_data"]
