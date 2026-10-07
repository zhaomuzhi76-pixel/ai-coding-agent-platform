"""L23 分层修复：根据审查报告修复可修复项（目录/__init__ 缺失）。"""
from __future__ import annotations

import json
from pathlib import Path

from backend.rag.ingest.review.tools.layer_registry import REPORT_DIR


def run_fix(scope: str, report_path: str | None) -> dict:
    report = _load(report_path)
    fixed: list[str] = []
    for _layer, info in report.get("layers", {}).items():
        for issue in info.get("findings", []):
            if _try_fix(issue):
                fixed.append(issue.get("file") or issue.get("path", ""))
        if info.get("reason") == "missing_dir" and info.get("path"):
            if _ensure_dir(Path(info["path"])):
                fixed.append(info["path"])
    result = {"scope": scope, "fixed": fixed, "count": len(fixed)}
    _write_summary(result)
    return result


def _load(path: str | None) -> dict:
    if not path:
        return {"layers": {}}
    p = Path(path)
    if not p.exists():
        return {"layers": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def _try_fix(issue: dict) -> bool:
    kind = issue.get("kind")
    if kind == "missing_init":
        return _ensure_dir(Path(issue["path"]).parent)
    return False


def _ensure_dir(root: Path) -> bool:
    if root.exists() and (root / "__init__.py").exists():
        return False
    root.mkdir(parents=True, exist_ok=True)
    init = root / "__init__.py"
    if not init.exists():
        init.write_text('"""L23 审核门子包。"""\n', encoding="utf-8")
    return True


def _write_summary(result: dict) -> None:
    out = Path(REPORT_DIR) / "fix-latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
