"""L2 用户规则参数覆盖：sqlite 里的 rule_param 记录 → checker args 覆盖。

设计（零硬编码）：
  · 用户说"单文件改为 200 行" → 存 kind=rule_param,
    key="file_size_max_230.max_lines", value="200"
  · rule_runner 执行前调 load_overrides(workspace) → 拿到
    {rule_id: {param: 值}}，叠加到 Rule.args
  · 类型转换：从原 args 现有值推断（int/float/str/list）

不重复职责：存储由 profile_ops，执行由 rule_runner，本模块只做"读+叠加"。
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from backend.agent_learning import profile_ops
from backend.agent_learning.scope import is_active_for
from backend.project_rules.rule_types import Rule


PARAM_KIND = "rule_param"


def _infer_type(s: str) -> Any:
    """模板为 None 时，按值的形态推断类型（零硬编码）。"""
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    # 整数
    if s.lstrip("-+").isdigit():
        try:
            return int(s)
        except ValueError:
            pass
    # 浮点
    try:
        if "." in s or "e" in low:
            return float(s)
    except ValueError:
        pass
    # 逗号分隔 → list
    if "," in s:
        return [x.strip() for x in s.split(",") if x.strip()]
    return s


def _coerce(raw: str, template: Any) -> Any:
    """按模板类型转换；模板为 None 时按值形态推断。"""
    s = str(raw).strip()
    if template is None:
        return _infer_type(s)
    if isinstance(template, bool):
        return s.lower() in ("1", "true", "yes", "on")
    if isinstance(template, int):
        try:
            return int(float(s))
        except ValueError:
            return template
    if isinstance(template, float):
        try:
            return float(s)
        except ValueError:
            return template
    if isinstance(template, (list, tuple)):
        parts = [x.strip() for x in s.split(",") if x.strip()]
        if isinstance(template, tuple):
            return tuple(parts)
        return parts
    return s


def load_overrides(workspace: str = "") -> dict[str, dict[str, Any]]:
    """从 sqlite 读取所有 rule_param，返回 {rule_id: {param: 值}}。

    工业级：同一 (rule_id, param) 若有多条历史值，取 last_used_at 最新。
    不依赖 confidence（用户最新一次修改为准）。
    """
    try:
        prefs = profile_ops.list_all(
            min_confidence=0, workspace=workspace,
        )
    except Exception:
        return {}
    # 按 (rule_id, param) 取 last_used_at 最新
    best: dict[tuple[str, str], tuple[float, Any]] = {}
    for p in prefs:
        if p.get("kind") != PARAM_KIND:
            continue
        if not is_active_for(
            p.get("scope", "global"),
            p.get("workspace", ""),
            workspace,
        ):
            continue
        key = str(p.get("key") or "")
        if "." not in key:
            continue
        rule_id, param = key.split(".", 1)
        ts = float(p.get("last_used_at") or 0)
        prev = best.get((rule_id, param))
        if prev is None or ts > prev[0]:
            best[(rule_id, param)] = (ts, p.get("value"))

    out: dict[str, dict[str, Any]] = {}
    for (rule_id, param), (_, val) in best.items():
        out.setdefault(rule_id, {})[param] = val
    return out


def apply_overrides(
    rule: Rule, overrides: dict[str, dict[str, Any]],
) -> Rule:
    """把用户覆盖叠加到单条 Rule.args。"""
    if rule.id not in overrides:
        return rule
    patch = overrides[rule.id]
    new_args = dict(rule.args or {})
    for param, raw_val in patch.items():
        template = new_args.get(param)
        new_args[param] = _coerce(raw_val, template)
    return replace(rule, args=new_args)


def apply_all(
    rules: list[Rule], workspace: str = "",
) -> list[Rule]:
    """一次性叠加所有覆盖。"""
    ov = load_overrides(workspace)
    if not ov:
        return rules
    return [apply_overrides(r, ov) for r in rules]


__all__ = [
    "PARAM_KIND", "load_overrides", "apply_overrides", "apply_all",
]
