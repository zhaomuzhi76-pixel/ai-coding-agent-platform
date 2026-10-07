"""别名回退守卫（单一职责：阻止对"双向词"的归一）。

场景：
  · alias_map.normalize_alias("芍药") → "白芍"（别名语义）
  · 但 TCMP 索引 211 的 class_name 本身就是 "芍药"（真名语义）
  · 归一反而把真名替换成索引里不存在的词 → 0 命中

策略：
  · PROTECTED 内：原样返回（不归一）
  · 其余：委托 alias_map.normalize_alias

加入 PROTECTED 的硬性条件：
  · 该词在 data/images/tcmp300/{train,val}/*/ 作为类名后缀存在（已确认）
  · 该词同时是 alias_map._ALIAS 的 key
"""
from __future__ import annotations

# 双向词：别名表里是 key，索引里也是真类名
PROTECTED = frozenset({"芍药"})


def apply_safe_alias(q: str, logger=None) -> str:
    """安全归一：命中 PROTECTED 的原词不替换，其余委托 normalize_alias。"""
    if not q:
        return q
    if q in PROTECTED:
        if logger:
            logger.debug("[alias_guard] protected: %r", q)
        return q
    try:
        from backend.rag.alias_map import normalize_alias
        n = normalize_alias(q)
        if n != q and logger:
            logger.info("[alias_guard] alias: %r → %r", q, n)
        return n
    except Exception:
        return q


def is_protected(q: str) -> bool:
    """判断 query 是否属于双向词守卫集。"""
    return bool(q) and q in PROTECTED


def list_protected() -> frozenset:
    """只读返回守卫集合快照。"""
    return PROTECTED
