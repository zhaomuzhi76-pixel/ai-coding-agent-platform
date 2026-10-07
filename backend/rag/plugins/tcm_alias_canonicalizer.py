"""TCM 别名反查（单一职责：用户说法 → 索引真实类名）。

背景：
  · alias_map 里 '芍药':'白芍'（方向与索引数据不符）
  · alias_map 是冻结文件，不能改
  · 本插件独立完成"反向归一"：白芍/赤芍/川赤芍 → 芍药

关键实现：
  · key 按长度降序匹配（避免"川赤芍"被"赤芍"抢先匹配）

env:
  RAG_TCM_CANON=0  关闭（默认 1）
"""
from __future__ import annotations
import os
from typing import Optional

# 用户说法 → 索引真实类名
_REVERSE = {
    "川赤芍": "芍药",
    "白芍": "芍药",
    "赤芍": "芍药",
    "芍药": "芍药",   # 幂等
    "生地": "地黄",
    "熟地": "地黄",
}

# 预排序：长 key 优先（避免子串抢先匹配）
_KEYS_SORTED = tuple(sorted(_REVERSE.keys(), key=len, reverse=True))


def _enabled() -> bool:
    v = os.environ.get("RAG_TCM_CANON", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def canonicalize(query: str) -> str:
    """query 里把别名替换为真实类名（长 key 优先 · 幂等）。"""
    if not query or not _enabled():
        return query
    out = query
    for k in _KEYS_SORTED:
        if k in out:
            out = out.replace(k, _REVERSE[k])
    return out


def lookup(name: str) -> Optional[str]:
    """单名查询：返回真实类名（无则 None）。"""
    if not name or not _enabled():
        return None
    return _REVERSE.get(name.strip())


def snapshot() -> dict:
    return {"enabled": _enabled(), "size": len(_REVERSE),
            "map": dict(_REVERSE), "keys_sorted": list(_KEYS_SORTED)}


__all__ = ["canonicalize", "lookup", "snapshot"]
