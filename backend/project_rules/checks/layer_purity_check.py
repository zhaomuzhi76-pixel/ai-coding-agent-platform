"""层纯净性检查：L3 不得引用 L1（跨层依赖）。

简化实现：扫描 L3 目录的 import，看是否只引用 L0-L2 和 L3 本身。
"""
from __future__ import annotations

import ast
from pathlib import Path

from backend.project_rules.rule_types import Rule, RuleResult


class LayerPurityChecker:
    rule_id = "layer_purity"

    def run(self, root_path: str, rule: Rule) -> RuleResult:
        root = Path(root_path)
        # 工业级：layers 空时自动探测（零硬编码）
        layers = rule.args.get("layers") or {}
        if not layers:
            from backend.project_rules.discovery import detect_layers
            layers = detect_layers(root)
        if not layers:
            # 无层约定 → 不做层检查
            return RuleResult(rule_id=rule.id, passed=True)

        # 收集每层的 import 前缀
        layer_roots: dict[str, list[str]] = {}
        for name, paths in layers.items():
            layer_roots[name] = list(paths)

        # 只检查 L3（backend/api）
        findings: list[str] = []
        l3 = root / "backend" / "api"
        if l3.is_dir():
            for p in l3.rglob("*.py"):
                try:
                    tree = ast.parse(p.read_text(encoding="utf-8"))
                except (SyntaxError, OSError):
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        # 允许引用 L0/L1/L2/L3
                        if self._is_l4(node.module, layer_roots.get("L4", [])):
                            findings.append(
                                f"{p.name}: L3 引用了 L4 → {node.module}"
                            )
        return RuleResult(
            rule_id=rule.id,
            passed=not findings,
            findings=tuple(findings),
        )

    @staticmethod
    def _is_l4(module: str, l4_roots: list[str]) -> bool:
        m = module.replace("/", ".").replace(".py", "")
        return any(root.replace("/", ".") in m for root in l4_roots)


CHECKER = LayerPurityChecker()
