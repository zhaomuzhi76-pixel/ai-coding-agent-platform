"""Docstring writer (阿里云: 注释生成).

从 AST 补全 docstring 骨架（Google 风格）。
不调 LLM；纯结构性占位，供后续 LLM 精修。
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DocstringDraft:
    target: str
    kind: str        # module | class | function
    docstring: str
    style: str = "google"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "kind": self.kind,
            "docstring": self.docstring,
            "style": self.style,
        }


class DocstringWriter:
    VERSION = "1.0"

    def generate(self, source: str) -> List[DocstringDraft]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        out: List[DocstringDraft] = []
        module_doc = ast.get_docstring(tree)
        if not module_doc:
            out.append(DocstringDraft(
                target="<module>", kind="module",
                docstring='"""TODO: module purpose.\n\n'
                          'Responsibilities:\n    - ...\n"""',
            ))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if ast.get_docstring(node):
                    continue
                out.append(DocstringDraft(
                    target=node.name, kind="class",
                    docstring='"""TODO: class responsibility.\n\n'
                              'Owns:\n    - ...\n'
                              'Does not own:\n    - ...\n"""',
                ))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node):
                    continue
                if node.name.startswith("_") and node.name != "__init__":
                    continue
                doc = self._fn_docstring(node)
                out.append(DocstringDraft(
                    target=node.name, kind="function", docstring=doc,
                ))
        return out

    @staticmethod
    def _fn_docstring(node) -> str:
        args = [a.arg for a in node.args.args
                if a.arg not in ("self", "cls")]
        lines = ['"""TODO: function purpose.', ""]
        if args:
            lines.append("Args:")
            for a in args:
                lines.append(f"    {a}: description")
            lines.append("")
        if node.returns is not None:
            lines.append("Returns:")
            lines.append("    description")
        lines.append('"""')
        return "\n".join(lines)

    def ready(self) -> bool:
        return True

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["DocstringDraft", "DocstringWriter"]
