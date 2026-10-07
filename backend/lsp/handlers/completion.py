"""LSP completion handler (bridges to completion engine)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.excellence.aliyun.completion import (
    CompletionContext, CompletionEngine,
)


def _position_to_offset(text: str, line: int, character: int) -> int:
    lines = text.split("\n")
    offset = 0
    for i in range(min(line, len(lines))):
        offset += len(lines[i]) + 1
    return offset + character


def handle_completion(
    params: Dict[str, Any],
    documents,
    engine: Optional[CompletionEngine] = None,
) -> List[Dict[str, Any]]:
    text_doc = params.get("textDocument") or {}
    uri = str(text_doc.get("uri", ""))
    doc = documents.get(uri)
    if doc is None:
        return []
    pos = params.get("position") or {}
    line = int(pos.get("line", 0))
    char = int(pos.get("character", 0))
    offset = _position_to_offset(doc.text, line, char)
    prefix = doc.text[:offset]
    suffix = doc.text[offset:]

    if engine is None:
        return []
    ctx = CompletionContext(
        prefix=prefix, suffix=suffix,
        language=doc.language_id, file_path=uri,
        max_candidates=5,
    )
    try:
        items = engine.complete(ctx)
    except Exception:
        return []
    return [
        {
            "label": c.text.split("\n", 1)[0][:80] or "<snippet>",
            "kind": 1,  # Text
            "detail": c.source,
            "insertText": c.text,
            "score": c.score,
        }
        for c in items
    ]


__all__ = ["handle_completion"]
