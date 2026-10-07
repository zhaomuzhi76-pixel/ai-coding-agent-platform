"""L23 后端探测 —— AST 扫描现有模块，输出可调用符号，不触发 import 崩溃。"""
from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path

TARGETS: dict[str, str] = {
    "vector_store": "backend/storage/vector_store.py",
    "bm25_index": "backend/rag/hybrid/bm25_index.py",
    "reranker": "backend/rag/reranker_server.py",
    "gate": "backend/quality/layer_dependency_gate.py",
}

MODULE_OF: dict[str, str] = {
    "vector_store": "backend.storage.vector_store",
    "bm25_index": "backend.rag.hybrid.bm25_index",
    "reranker": "backend.rag.reranker_server",
    "gate": "backend.quality.layer_dependency_gate",
}


def probe_all(targets: list[str] | None) -> dict:
    names = targets or list(TARGETS.keys())
    return {name: _probe_one(name) for name in names}


def _probe_one(name: str) -> dict:
    path = Path(TARGETS[name])
    result: dict = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        result["symbols"] = []
        return result
    result["symbols"] = _scan_symbols(path)
    ok, err = _try_import(MODULE_OF[name])
    result["import_ok"] = ok
    result["import_error"] = err
    return result


def _scan_symbols(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        return [{"kind": "parse_error", "msg": f"{type(e).__name__}: {e}"}]
    out: list[dict] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(_fn_sig(node))
        elif isinstance(node, ast.ClassDef):
            out.append(_class_sig(node))
        elif isinstance(node, ast.Assign):
            out.extend(_assign_sig(node))
    return out


def _fn_sig(node) -> dict:
    args = [a.arg for a in node.args.args]
    return {"kind": "def", "name": node.name, "args": args, "line": node.lineno}


def _class_sig(node) -> dict:
    methods = [
        n.name for n in node.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return {"kind": "class", "name": node.name,
            "methods": methods[:20], "line": node.lineno}


def _assign_sig(node: ast.Assign) -> list[dict]:
    out = []
    for t in node.targets:
        if isinstance(t, ast.Name):
            kind = "assign_call" if isinstance(node.value, ast.Call) else "assign"
            out.append({"kind": kind, "name": t.id, "line": node.lineno})
    return out


def _try_import(module: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def render(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)
