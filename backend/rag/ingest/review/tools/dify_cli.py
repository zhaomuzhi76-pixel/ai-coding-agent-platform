"""L23 Dify 工作流 CLI —— 导出 / 校验 / 预览。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.rag.ingest.review.review.dify_workflow_builder import build_workflow

_DEFAULT_OUT = ".layer-review/dify_workflow.json"
_REQUIRED_NODE_TYPES = {"start", "end", "human-input", "code"}


def run_dify(action: str, output: str | None) -> dict:
    if action == "export":
        return _export(output or _DEFAULT_OUT)
    if action == "check":
        return _check(output or _DEFAULT_OUT)
    return {"ok": False, "reason": f"unknown action: {action}"}


def _export(path: str) -> dict:
    wf = build_workflow()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True, "action": "export", "path": str(p),
        "nodes": len(wf["workflow"]["graph"]["nodes"]),
        "edges": len(wf["workflow"]["graph"]["edges"]),
    }


def _check(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"ok": False, "reason": "file_not_found", "path": str(p)}
    try:
        wf = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "reason": f"parse_error: {e}"}
    issues = _validate(wf)
    return {"ok": not issues, "path": str(p), "issues": issues}


def _validate(wf: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if "app" not in wf or "workflow" not in wf:
        issues.append("missing top-level 'app' or 'workflow'")
        return issues
    graph = wf["workflow"].get("graph") or {}
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    if not nodes:
        issues.append("no nodes")
    types = {n.get("type") for n in nodes}
    missing = _REQUIRED_NODE_TYPES - types
    if missing:
        issues.append(f"missing node types: {sorted(missing)}")
    ids = {n.get("id") for n in nodes}
    for e in edges:
        for end in ("source", "target"):
            if e.get(end) not in ids:
                issues.append(f"edge {e.get('id')} has dangling {end}={e.get(end)}")
    hi = [n for n in nodes if n.get("type") == "human-input"]
    if not hi:
        issues.append("no human-input node")
    else:
        acts = (hi[0].get("data") or {}).get("actions") or []
        if len(acts) < 3:
            issues.append(f"human-input needs >=3 actions, got {len(acts)}")
    return issues
