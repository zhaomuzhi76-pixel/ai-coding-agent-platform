"""Test generator (阿里云: 单测生成).

从函数签名生成 pytest 骨架，不调 LLM；纯静态骨架 + 占位断言。
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FunctionSpec:
    name: str
    args: List[str] = field(default_factory=list)
    is_async: bool = False
    returns: str = ""
    decorators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "args": list(self.args),
            "is_async": self.is_async,
            "returns": self.returns,
            "decorators": list(self.decorators),
        }


@dataclass
class TestDraft:
    target_module: str
    target_name: str
    source: str
    function_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_module": self.target_module,
            "target_name": self.target_name,
            "function_count": self.function_count,
            "source": self.source,
        }


class TestGenerator:
    VERSION = "1.0"

    def parse_functions(self, source: str) -> List[FunctionSpec]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        out: List[FunctionSpec] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                args = [a.arg for a in node.args.args
                        if a.arg not in ("self", "cls")]
                decorators = []
                for d in node.decorator_list:
                    if isinstance(d, ast.Name):
                        decorators.append(d.id)
                returns = (
                    ast.unparse(node.returns)
                    if node.returns is not None else ""
                )
                out.append(FunctionSpec(
                    name=node.name, args=args,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    returns=returns, decorators=decorators,
                ))
        return out

    def generate(
        self,
        module_path: str,
        source: str,
        *,
        max_funcs: int = 10,
    ) -> TestDraft:
        module_name = (
            module_path.replace("/", ".").replace("\\", ".")
            .removesuffix(".py")
        )
        specs = self.parse_functions(source)[:max_funcs]
        if not specs:
            return TestDraft(
                target_module=module_name,
                target_name="<no_public_funcs>",
                source="# no public function found\n",
                function_count=0,
            )
        import_name = module_name.split(".")[-1]
        lines = [
            '"""Auto-generated pytest skeleton."""',
            "from __future__ import annotations",
            "",
            "import pytest",
            f"from {module_name} import {import_name}  # noqa",
            "",
        ]
        for spec in specs:
            lines.extend(self._render_test(spec))
        return TestDraft(
            target_module=module_name,
            target_name=specs[0].name,
            source="\n".join(lines),
            function_count=len(specs),
        )

    @staticmethod
    def _render_test(spec: FunctionSpec) -> List[str]:
        lines = [f"def test_{spec.name}():", "    # TODO: arrange"]
        if spec.args:
            args = ", ".join(f"arg_{a}" for a in spec.args)
            lines.append(f"    # call with: {args}")
        if spec.is_async:
            lines.append(f"    # async function: use asyncio.run")
        lines.append("    # TODO: act")
        lines.append("    # TODO: assert")
        lines.append("    assert True")
        lines.append("")
        return lines

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["FunctionSpec", "TestDraft", "TestGenerator"]
