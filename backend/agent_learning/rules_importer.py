"""L2 .rules 导入器：解析 → upsert 到 sqlite。

不重复职责：
  - 解析 → rules_parser.py
  - 存储 → profile_ops.upsert
  - 本模块只做"编排 + scope/workspace 绑定"
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from pathlib import Path
from typing import Any

from backend.agent_learning import profile_ops
from backend.agent_learning.rules_contract import Rule
from backend.agent_learning.rules_parser import parse_file
from backend.agent_learning.scope import RuleScope


def import_file(
    path: str | Path,
    *,
    workspace: str = "",
    scope: str = RuleScope.PROJECT.value,
    confidence: int = 95,
) -> dict[str, Any]:
    """导入单个 .rules 文件。workspace 默认文件所在目录。"""
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": f"file not found: {p}"}
    if not workspace:
        workspace = str(p.parent)
    result = parse_file(p)
    imported = _upsert_rules(result.rules, workspace, scope, confidence)
    return {
        "ok": result.ok,
        "source_path": str(p),
        "workspace": workspace,
        "scope": scope,
        "parsed": len(result.rules),
        "imported": imported,
        "errors": result.errors,
    }


def import_rules(
    rules: list[Rule], *,
    workspace: str, scope: str = RuleScope.PROJECT.value,
    confidence: int = 95,
) -> int:
    return _upsert_rules(rules, workspace, scope, confidence)


def _upsert_rules(
    rules: list[Rule], workspace: str, scope: str, confidence: int,
) -> int:
    count = 0
    for r in rules:
        try:
            profile_ops.upsert(
                kind=r.kind, key=r.key, value=r.value,
                confidence=confidence, scope=scope, workspace=workspace,
            )
            count += 1
        except Exception as e:
            swallow("agent_learning.rules_importer:66", e)
    return count


__all__ = ["import_file", "import_rules"]
