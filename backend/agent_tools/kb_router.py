"""KB 路由器（单一职责：query → kb 标签）。

问题：runtime.py 里 RagToolSpec 硬编码 where={"kb":"xxx"}
     但 chroma collection 只有一个（agent_code_knowledge）
     且 metadata 里无 kb 字段 → where 过滤后 0 命中

策略：本模块给出两档策略
  · route(query) → Optional[str]   有信号才返回 kb 标签
  · is_effective() → bool           决定是否启用 where 过滤

env 可覆盖：
  RAG_KB_FILTER_ENABLED=0          强制关闭 kb 过滤（默认 0）
  RAG_KB_ROUTE_MAP='tcm=中医,中药;agriculture=小麦,作物'
"""
from __future__ import annotations
import os
from typing import Optional, Tuple


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


# 默认 kb 路由（语义关键词，非硬编码逻辑；env 可覆盖）
_DEFAULT_MAP: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("tcm",         ("中医","中药","方剂","药材","性味","归经","气血","经络")),
    ("agriculture", ("农业","作物","种植","小麦","玉米","水稻","病虫害","防治")),
    ("finance",     ("金融","投资","股票","基金","保险","证券","理财")),
    ("general",     ("通用","常识","百科")),
)


def _load_map():
    raw = os.environ.get("RAG_KB_ROUTE_MAP")
    if not raw:
        return _DEFAULT_MAP
    out = []
    for pair in raw.split(";"):
        if "=" not in pair:
            continue
        kb, kws = pair.split("=", 1)
        kws = tuple(k.strip() for k in kws.split(",") if k.strip())
        if kb.strip() and kws:
            out.append((kb.strip(), kws))
    return tuple(out) or _DEFAULT_MAP


def is_enabled() -> bool:
    """kb 过滤是否启用（默认关闭，因 chroma 里无 kb metadata）。"""
    return _env_bool("RAG_KB_FILTER_ENABLED", False)


def route(query: str) -> Optional[str]:
    """按 query 语义关键词路由到 kb 标签；无匹配返回 None。"""
    if not query or not is_enabled():
        return None
    q = query
    best = None
    best_hits = 0
    for kb, kws in _load_map():
        hits = sum(1 for k in kws if k in q)
        if hits > best_hits:
            best_hits = hits
            best = kb
    return best if best_hits > 0 else None


def effective_where(default_kb: Optional[str], query: str) -> Optional[dict]:
    """返回是否启用 where：
      · kb 过滤关闭 → None（不过滤）
      · 路由命中 → {"kb": <命中>}
      · 路由未命中但有 default_kb → None（不用 default，避免误过滤）
    """
    if not is_enabled():
        return None
    kb = route(query)
    if kb:
        return {"kb": kb}
    return None


def snapshot() -> dict:
    return {
        "enabled": is_enabled(),
        "map_size": len(_load_map()),
        "map": [(kb, list(kws)) for kb, kws in _load_map()],
    }
