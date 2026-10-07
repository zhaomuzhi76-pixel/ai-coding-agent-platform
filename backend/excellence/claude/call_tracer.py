"""CallTracer: track symbol call chains (Claude Code: 调用链追踪).

与 code_intelligence.GraphProvider 的区别：
    GraphProvider -> 静态依赖图（含 module / class / func / import 边）
    CallTracer    -> 只追踪「从入口到符号」的定向调用路径（带深度限制）
"""
from __future__ import annotations

import ast
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

_SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}


@dataclass
class CallNode:
    module: str
    name: str

    def key(self) -> str:
        return f"{self.module}::{self.name}"

    def to_dict(self) -> Dict[str, Any]:
        return {"module": self.module, "name": self.name}


@dataclass
class CallChain:
    target: CallNode
    chain: List[CallNode] = field(default_factory=list)

    @property
    def depth(self) -> int:
        return len(self.chain)

    def as_str(self) -> str:
        return " -> ".join(n.key() for n in self.chain)

    def dump(self) -> Dict[str, Any]:
        return {
            "target": self.target.to_dict(),
            "depth": self.depth,
            "chain": [n.to_dict() for n in self.chain],
        }


class CallTracer:
    """Build a static call graph and trace paths to a target symbol."""

    VERSION = "1.0"

    def __init__(self, max_depth: int = 6) -> None:
        if max_depth <= 0:
            raise ValueError("max_depth must positive")
        self._max_depth = max_depth
        self._calls: Dict[str, Set[str]] = defaultdict(set)

    def index(self, root: str) -> int:
        """Index all .py files under root; return number of edges."""
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS]
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(base, name)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                mod = rel[:-3].replace("/", ".")
                try:
                    with open(path, "r", encoding="utf-8",
                              errors="ignore") as fh:
                        tree = ast.parse(fh.read())
                except (OSError, SyntaxError):
                    continue
                self._index_module(mod, tree)
        return sum(len(v) for v in self._calls.values())

    def _index_module(self, module: str, tree: ast.Module) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller = f"{module}::{node.name}"
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        callee = self._callee_name(sub)
                        if callee:
                            self._calls[caller].add(
                                f"{module}::{callee}"
                            )

    @staticmethod
    def _callee_name(call: ast.Call) -> Optional[str]:
        fn = call.func
        if isinstance(fn, ast.Name):
            return fn.id
        if isinstance(fn, ast.Attribute):
            return fn.attr
        return None

    def callers_of(self, target_key: str, limit: int = 50) -> List[str]:
        out: List[str] = []
        for caller, callees in self._calls.items():
            if target_key in callees:
                out.append(caller)
                if len(out) >= limit:
                    break
        return out

    def trace_to(
        self, target_module: str, target_name: str,
    ) -> List[CallChain]:
        """Find caller chains leading to target (BFS, up to max_depth)."""
        target = CallNode(target_module, target_name)
        target_key = target.key()
        chains: List[CallChain] = []
        frontier = [(target, [target])]
        seen: Set[str] = {target_key}
        for _ in range(self._max_depth):
            next_frontier = []
            for node, path in frontier:
                for caller in self.callers_of(node.key()):
                    if caller in seen:
                        continue
                    seen.add(caller)
                    try:
                        mod, _, name = caller.partition("::")
                    except ValueError:
                        continue
                    cn = CallNode(mod, name)
                    new_path = [cn] + path
                    chains.append(CallChain(target=target, chain=new_path))
                    next_frontier.append((cn, new_path))
            if not next_frontier:
                break
            frontier = next_frontier
        return chains

    def edge_count(self) -> int:
        return sum(len(v) for v in self._calls.values())

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "edges": self.edge_count(),
            "max_depth": self._max_depth,
        }


__all__ = ["CallNode", "CallChain", "CallTracer"]
