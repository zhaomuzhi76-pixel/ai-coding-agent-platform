"""L2 规则冲突检测。

工业级：按 (scope, workspace) 分组检测 —— 不同项目之间不算冲突。
不重复职责：只做检测，不做修复。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend.agent_learning.rules_contract import Conflict, Rule

_SINGLETON_KEYS = frozenset({"max_lines", "naming", "python_version"})
_OPPOSITE: dict[str, str] = {"forbid": "require", "require": "forbid"}


def detect(rules: list[Rule]) -> list[Conflict]:
    """对一组规则做冲突检测。"""
    out: list[Conflict] = []
    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for r in rules:
        grouped[(r.kind, r.key)].append(r.value)

    for (kind, key), values in grouped.items():
        uniq = list(dict.fromkeys(values))

        if key in _SINGLETON_KEYS and len(uniq) > 1:
            out.append(Conflict(
                kind=kind, key=key, values=tuple(uniq),
                reason=f"`{key}` 只能有一个值",
            ))
            continue

        if key in _OPPOSITE:
            opp_kind, opp_key = kind, _OPPOSITE[key]
            opp_values = set(grouped.get((opp_kind, opp_key), []))
            for v in uniq:
                if v in opp_values:
                    out.append(Conflict(
                        kind=kind, key=key, values=(v,),
                        reason=(f"`{key}={v}` 与 "
                                f"`{opp_key}={v}` 语义相反"),
                    ))
    return out


def detect_from_sqlite(workspace: str = "") -> list[Conflict]:
    """按 (scope, workspace) 分组检测 —— 不同项目之间不算冲突。

    分组规则：
      - global 规则 → 单一分组 ("global", "")
      - project/session 规则 → 按 workspace 独立分组
    """
    from backend.agent_learning import profile_ops

    prefs = profile_ops.list_all(min_confidence=0, workspace=workspace)
    groups: dict[tuple[str, str], list[Rule]] = defaultdict(list)
    for p in prefs:
        scope = p.get("scope", "global") or "global"
        ws = p.get("workspace", "") or ""
        key = (scope, ws) if scope in ("project", "session") \
            else ("global", "")
        groups[key].append(Rule(
            kind=p["kind"], key=p["key"], value=p["value"],
        ))

    out: list[Conflict] = []
    for (scope, ws), rules in groups.items():
        for c in detect(rules):
            tag = f"[{scope} {ws}]" if ws else f"[{scope}]"
            out.append(Conflict(
                kind=c.kind, key=c.key, values=c.values,
                severity=c.severity, reason=f"{tag} {c.reason}",
            ))
    return out


def summarize(conflicts: list[Conflict]) -> dict[str, Any]:
    errors = [c for c in conflicts if c.severity == "error"]
    return {
        "total": len(conflicts),
        "errors": len(errors),
        "warnings": len(conflicts) - len(errors),
        "items": [c.to_dict() for c in conflicts],
    }


__all__ = ["detect", "detect_from_sqlite", "summarize"]
