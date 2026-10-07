"""中医古籍权威分级加载器（工业级）。
从 backend/data/tcm_classics.yaml 读分级，提供 priority 查询。
环境变量：RAG_TCM_CLASSICS_PATH= 自定义 yaml 路径
"""
from __future__ import annotations
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_YAML_ENV = os.environ.get("RAG_TCM_CLASSICS_PATH", "")


def _yaml_path() -> Path:
    if _YAML_ENV:
        return Path(_YAML_ENV)
    return Path(__file__).resolve().parents[1] / "data" / "tcm_classics.yaml"


_lock = threading.Lock()
_cache: Optional[List[Tuple[int, str]]] = None


def _parse_yaml_simple(text: str) -> Dict[str, List[str]]:
    """极简 YAML 解析（只支持 tier_N:\n  - item），无依赖。"""
    out: Dict[str, List[str]] = {}
    cur_key: Optional[str] = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("-"):
            cur_key = stripped[:-1].strip()
            if "#" in cur_key:
                cur_key = cur_key.split("#", 1)[0].strip()
            out.setdefault(cur_key, [])
            continue
        if stripped.startswith("- ") and cur_key:
            item = stripped[2:].strip()
            if "#" in item:
                item = item.split("#", 1)[0].strip()
            if item:
                out[cur_key].append(item)
    return out


def _load() -> List[Tuple[int, str]]:
    global _cache
    with _lock:
        if _cache is not None:
            return _cache
        p = _yaml_path()
        entries: List[Tuple[int, str]] = []
        if p.is_file():
            try:
                data = _parse_yaml_simple(p.read_text(encoding="utf-8"))
                for key, items in data.items():
                    if not key.startswith("tier_"):
                        continue
                    try:
                        tier = int(key.split("_", 1)[1])
                    except ValueError:
                        continue
                    for name in items:
                        entries.append((tier, name))
            except Exception:
                pass
        entries.sort(key=lambda x: (x[0], len(x[1])))
        _cache = entries
        return entries


def reload() -> None:
    global _cache
    with _lock:
        _cache = None


def priority_of(source: str) -> int:
    """返回方源优先级：tier (1~5) 或 99（非古籍）。"""
    if not source:
        return 99
    s = str(source)
    best: Optional[int] = None
    for tier, name in _load():
        if name in s:
            if best is None or tier < best:
                best = tier
    return best if best is not None else 99


def list_all() -> List[Tuple[int, str]]:
    return list(_load())


__all__ = ["priority_of", "list_all", "reload"]
