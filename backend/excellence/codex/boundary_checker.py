"""Import / API boundary checker (Codex: 类型、安全、边界检查).

与 workspace.WorkspaceBoundaryGuard 的区别：
    BoundaryGuard    -> 语义职责冲突（人类可读的责任描述相似度）
    BoundaryChecker  -> 硬结构约束（import 方向 + 新增 API 签名）
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


def _to_module(name: str) -> str:
    """Normalize 'backend/core/foo.py' -> 'backend.core.foo'."""
    n = name.replace("\\", "/")
    if n.endswith(".py"):
        n = n[:-3]
    return n.replace("/", ".")


@dataclass
class BoundaryViolation:
    kind: str        # forbidden_import | public_api_change | circular
    source: str
    target: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "target": self.target,
            "detail": self.detail,
        }


@dataclass
class BoundaryReport:
    violations: List[BoundaryViolation] = field(default_factory=list)
    checked_imports: int = 0

    @property
    def ok(self) -> bool:
        return not self.violations

    def dump(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "checked_imports": self.checked_imports,
            "violations": [v.to_dict() for v in self.violations],
        }


class BoundaryChecker:
    """Check imports against a forbidden-edge list.

    Source/target 内部一律用模块名匹配（路径会被自动转换）。
    """

    VERSION = "1.1"

    def __init__(self) -> None:
        self._forbidden: Set[tuple] = set()

    def forbid(self, source_prefix: str, target_prefix: str) -> None:
        sf = _to_module(source_prefix)
        tf = _to_module(target_prefix)
        self._forbidden.add((sf, tf))

    def check_source(
        self,
        source_path: str,
        source_text: str,
        *,
        module_name: str = "",
    ) -> BoundaryReport:
        report = BoundaryReport()
        src_module = _to_module(module_name or source_path)
        try:
            tree = ast.parse(source_text)
        except SyntaxError as exc:
            report.violations.append(BoundaryViolation(
                kind="forbidden_import",
                source=src_module,
                target="<syntax_error>",
                detail=str(exc),
            ))
            return report
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    report.checked_imports += 1
                    self._check_edge(src_module, a.name, report)
            elif isinstance(node, ast.ImportFrom) and node.module:
                report.checked_imports += 1
                self._check_edge(src_module, node.module, report)
        return report

    def _check_edge(
        self, src: str, target: str, report: BoundaryReport,
    ) -> None:
        for sf, tf in self._forbidden:
            if src.startswith(sf) and target.startswith(tf):
                report.violations.append(BoundaryViolation(
                    kind="forbidden_import", source=src, target=target,
                    detail=f"edge {sf} -> {tf} forbidden",
                ))
                return

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "rules": len(self._forbidden),
        }


__all__ = ["BoundaryViolation", "BoundaryReport", "BoundaryChecker"]
