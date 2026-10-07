"""L2 规则继承：祖先目录 .rules 递归合并。

工业级：和 .gitignore / .cursorrules 一致 —— 子目录覆盖父目录。

优先级：子孙 > 祖先
  /a/.rules          ← 最低
  /a/b/.rules        ← 中
  /a/b/c/.rules      ← 最高（覆盖前两个）
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.agent_learning.rules_contract import Rule
from backend.agent_learning.rules_parser import parse_file


#: 支持的规则文件名（按优先级）
_FILENAMES = (".biancheng.rules", ".rules")


def find_ancestor_rules(
    workspace: str, *, stop_at: str = "",
) -> list[Path]:
    """从 workspace 向上找所有 .rules 文件（不含 workspace 本身）。"""
    if not workspace:
        return []
    stop = Path(stop_at).resolve() if stop_at else None
    found: list[Path] = []
    p = Path(workspace).resolve()
    cur = p.parent
    while cur != cur.parent:
        if stop is not None and cur == stop:
            break
        for fname in _FILENAMES:
            f = cur / fname
            if f.is_file():
                found.append(f)
                break
        cur = cur.parent
    return found


def load_inherited(workspace: str) -> list[tuple[Path, list[Rule]]]:
    """返回 [(file, rules), ...]，从祖先到子孙排序。"""
    files: list[Path] = []
    files.extend(reversed(find_ancestor_rules(workspace)))
    # 最后加 workspace 自己的
    p = Path(workspace)
    for fname in _FILENAMES:
        f = p / fname
        if f.is_file():
            files.append(f)
            break

    out: list[tuple[Path, list[Rule]]] = []
    for f in files:
        r = parse_file(f)
        if r.ok and r.rules:
            out.append((f, list(r.rules)))
    return out


def merge_inherited(workspace: str) -> dict[str, Any]:
    """合并结果：子孙覆盖祖先。返回 {kind.key: value, ...}。"""
    merged: dict[str, str] = {}
    sources: list[str] = []
    for f, rules in load_inherited(workspace):
        sources.append(str(f))
        for r in rules:
            merged[f"{r.kind}.{r.key}"] = r.value
    return {
        "workspace": workspace,
        "sources": sources,
        "rule_count": len(merged),
        "rules": merged,
    }


__all__ = [
    "find_ancestor_rules", "load_inherited", "merge_inherited",
]
