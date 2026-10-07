"""L23 分层审查：AST 跨层 import 扫描 + 单文件行数限制。"""
from __future__ import annotations

import ast
import json
from pathlib import Path

from backend.rag.ingest.review.tools.layer_registry import (
    LAYER_NAMES,
    LAYER_ORDER,
    MAX_LINES,
    REVIEW_PREFIX,
    module_of,
    module_path,
)


def run_gate(layers: list[str] | None, output: str | None) -> dict:
    targets = layers or list(LAYER_NAMES)
    report: dict = {"layers": {}, "ok": True}
    for name in targets:
        result = _audit_layer(name)
        report["layers"][name] = result
        report["ok"] = report["ok"] and bool(result.get("ok"))
    if output:
        _write(output, report)
    return report


def _audit_layer(name: str) -> dict:
    try:
        root = Path(module_path(module_of(name)))
    except KeyError as e:
        return {"ok": False, "reason": "unknown_layer", "msg": str(e)}
    if not root.exists():
        return {"ok": False, "reason": "missing_dir", "path": str(root)}
    findings: list[dict] = []
    files = sorted(p for p in root.rglob("*.py"))
    for f in files:
        findings.extend(_scan_file(f))
    return {
        "ok": not findings,
        "path": str(root),
        "files": len(files),
        "findings": findings,
    }


def _scan_file(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [{"file": str(path), "kind": "read_error", "msg": str(e)}]
    issues: list[dict] = []
    if len(text.splitlines()) > MAX_LINES:
        issues.append({
            "file": str(path),
            "kind": "line_limit",
            "msg": f">{MAX_LINES} lines",
        })
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        issues.append({"file": str(path), "kind": "syntax_error", "msg": str(e)})
        return issues
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            bad = _check_import(path, node)
            if bad:
                issues.append(bad)
    return issues


def _check_import(path: Path, node: ast.ImportFrom) -> dict | None:
    module = node.module or ""
    if not module.startswith(REVIEW_PREFIX):
        return None
    tail = module[len(REVIEW_PREFIX):]
    target = tail.split(".")[0]
    if target not in LAYER_ORDER:
        return None
    current = _current_layer(path)
    if current is None:
        return None
    if LAYER_ORDER[target] > LAYER_ORDER[current]:
        return {
            "file": str(path),
            "kind": "cross_layer_import",
            "from": current,
            "to": target,
            "line": node.lineno,
        }
    return None


def _current_layer(path: Path) -> str | None:
    parts = list(path.parts)
    try:
        idx = parts.index("review")
    except ValueError:
        return None
    if idx + 1 < len(parts):
        candidate = parts[idx + 1]
        if candidate in LAYER_ORDER:
            return candidate
    return None


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
