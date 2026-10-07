"""分层依赖门禁：禁止反向依赖。"""
from __future__ import annotations

import ast
import os
from typing import Dict, FrozenSet, Iterator, List, Set

from backend.quality.gate_contract import GateContext, GateResult, GateViolation

LAYER_ORDER: List[str] = [
    "core", "quality", "config", "storage", "registry",
    "knowledge", "code_intelligence", "providers",
    "workspace", "runtime", "persistence",
    "agent", "application", "assembly",
    "api", "system", "process", "tests",
]

# 有文档的例外：文件 -> 允许的导入模块集合。
KNOWN_EXCEPTIONS: Dict[str, Set[str]] = {
    "runtime/executors/code_modify_executor/executor.py": {
        "backend.application.planning.workspace_path_normalizer",
    },
    "runtime/executors/multi_file_modify_executor/validator.py": {
        "backend.application.planning.workspace_path_normalizer",
    },
    "runtime/executors/project_analysis_executor.py": {
        "backend.application.planning.workspace_path_normalizer",
    },
    "runtime/executors/error_fix_executor.py": {
        "backend.application.planning.workspace_path_normalizer",
    },
    "persistence/plugins/project_persistence_startup_factory.py": {
        "backend.assembly.startup_module",
    },
    "persistence/plugins/persistence_startup_assembly_adapter.py": {
        "backend.assembly.startup_module",
    },
    "persistence/plugins/project_session_persistence_startup_factory.py": {
        "backend.assembly.startup_module",
    },
}

EXCEPTION_META: Dict[str, Dict[str, str]] = {
    "backend.application.planning.workspace_path_normalizer": {
        "reason": "纯字符串工具，被错放在 application 层",
        "fix_plan": "迁到 backend/workspace/paths/normalizer.py",
        "expires": "2026-Q2",
    },
    "backend.assembly.startup_module": {
        "reason": "启动期装配，持久化插件在启动时反向引用是设计需要",
        "fix_plan": "迁到 backend/core/startup/module.py",
        "expires": "2026-Q2",
    },
}


def _normalize(module: str) -> str:
    return module[len("backend."):] if module.startswith("backend.") else module


def _layer_of(module: str) -> int:
    m = _normalize(module)
    for idx, prefix in enumerate(LAYER_ORDER):
        if m == prefix or m.startswith(prefix + "."):
            return idx
    return -1


class LayerDependencyGate:
    name = "layer_dependency"
    layer = "quality"

    def run(self, ctx: GateContext) -> GateResult:
        violations: List[GateViolation] = []
        metrics = {
            "files": 0, "imports": 0, "skipped": 0,
            "excepted": 0, "layers": len(LAYER_ORDER),
        }
        for path in self._iter_py(ctx.root):
            rel = os.path.relpath(path, ctx.root).replace(os.sep, "/")
            module = rel[:-3].replace("/", ".")
            src_layer = _layer_of(module)
            if src_layer < 0:
                metrics["skipped"] += 1
                continue
            metrics["files"] += 1
            allowed: FrozenSet[str] = frozenset(KNOWN_EXCEPTIONS.get(rel, ()))
            for imported in self._imports(path):
                metrics["imports"] += 1
                dst_layer = _layer_of(imported)
                if dst_layer < 0 or dst_layer <= src_layer:
                    continue
                if imported in allowed:
                    metrics["excepted"] += 1
                    continue
                violations.append(GateViolation(
                    code="LAYER_REVERSE_DEP",
                    message=f"{rel} ({LAYER_ORDER[src_layer]}) imports {imported}",
                    location=rel,
                    severity="error",
                ))
        return GateResult(
            name=self.name, passed=not violations,
            violations=violations, metrics=metrics,
        )

    @staticmethod
    def _iter_py(root: str) -> Iterator[str]:
        skip = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in skip]
            for name in files:
                if name.endswith(".py"):
                    yield os.path.join(base, name)

    @staticmethod
    def _imports(path: str) -> List[str]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                tree = ast.parse(fh.read())
        except (SyntaxError, OSError):
            return []
        found: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                found.add(node.module)
        return sorted(found)
