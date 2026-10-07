"""规则加载器：从 rules.yaml 读规则。

Responsibility:
    - 读 yaml → 校验 → 返回 list[Rule]
    - lru_cache 缓存（同进程内二次读零磁盘 IO）
Not Responsible:
    - 校验规则结构（那是 rule_schema）
    - 执行规则
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

from .rule_schema import parse_all
from .rule_types import Rule

_ENV = "LOCO_PROJECT_RULES"


def _resolve_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get(_ENV)
    if env:
        return Path(env)
    return Path(__file__).with_name("rules.yaml")


@lru_cache(maxsize=4)
def _load_cached(path_str: str) -> tuple[Rule, ...]:
    raw = yaml.safe_load(Path(path_str).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("rules.yaml root must be object")
    return tuple(parse_all(raw.get("rules") or []))


def load_rules(path: str | None = None) -> list[Rule]:
    p = _resolve_path(path)
    if not p.is_file():
        raise FileNotFoundError(f"rules file not found: {p}")
    return list(_load_cached(str(p)))


def clear_cache() -> None:
    _load_cached.cache_clear()


__all__ = ["load_rules", "clear_cache"]
