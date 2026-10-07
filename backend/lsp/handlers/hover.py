"""LSP hover handler: minimal docstring lookup via AST."""
from __future__ import annotations

import ast
from typing import Any, Dict, Optional


def _word_at(text: str, line: int, char: int) -> str:
    lines = text.split("\n")
    if line >= len(lines):
        return ""
    src = lines[line]
    lo = char
    hi = char
    while lo > 0 and (src[lo - 1].isalnum() or src[lo - 1] == "_"):
        lo -= 1
    while hi < len(src) and (src[hi].isalnum() or src[hi] == "_"):
        hi += 1
    return src[lo:hi]


def _find_docstring(text: str, name: str) -> Optional[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            if node.name == name:
                doc = ast.get_docstring(node)
                return doc or f"`{name}` (no docstring)"
    return None


def handle_hover(
    params: Dict[str, Any], documents,
) -> Optional[Dict[str, Any]]:
    text_doc = params.get("textDocument") or {}
    uri = str(text_doc.get("uri", ""))
    doc = documents.get(uri)
    if doc is None:
        return None
    pos = params.get("position") or {}
    name = _word_at(doc.text,
                    int(pos.get("line", 0)),
                    int(pos.get("character", 0)))
    if not name:
        return None
    info = _find_docstring(doc.text, name)
    if info is None:
        return None
    return {
        "contents": {"kind": "markdown", "value": info},
        "range": None,
    }


__all__ = ["handle_hover"]
