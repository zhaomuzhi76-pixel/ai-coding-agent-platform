"""LSP diagnostics handler (bridges to rule reviewer)."""
from __future__ import annotations

from typing import Any, Dict, List

from backend.excellence.aliyun.rule_review import RuleReviewer


_SEVERITY_MAP = {"error": 1, "warning": 2, "info": 3}


def handle_diagnostics(
    params: Dict[str, Any],
    documents,
    reviewer: RuleReviewer,
) -> List[Dict[str, Any]]:
    text_doc = params.get("textDocument") or {}
    uri = str(text_doc.get("uri", ""))
    doc = documents.get(uri)
    if doc is None:
        return []
    if not doc.language_id == "python" and not uri.endswith(".py"):
        return []
    try:
        report = reviewer.review(uri, doc.text)
    except Exception:
        return []
    return [
        {
            "range": {
                "start": {"line": 0, "character": 0},
                "end": {"line": 0, "character": 80},
            },
            "severity": _SEVERITY_MAP.get(v.level, 3),
            "source": "backend-lsp",
            "code": v.rule,
            "message": f"[{v.dimension}] {v.message}",
        }
        for v in report.violations
    ]


__all__ = ["handle_diagnostics"]
