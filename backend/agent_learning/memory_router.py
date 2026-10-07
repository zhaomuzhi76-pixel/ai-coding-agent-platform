"""L3 HTTP 路由 —— /api/memory/*。"""
from __future__ import annotations

from typing import Any

from backend.agent_learning import profile_ops
from backend.agent_learning.extractor import LlmExtractor, RuleExtractor

PREFIX = "/api/memory"
_rule = RuleExtractor()
_llm = LlmExtractor()


def build_router() -> Any:
    try:
        from fastapi import APIRouter, Body, Query  # type: ignore
    except Exception:
        return None
    router = APIRouter()

    @router.get(f"{PREFIX}/preferences")
    def list_prefs(
        min_confidence: int = Query(30),
        scope: str = Query(""),
        workspace: str = Query(""),
    ) -> dict:
        return {"preferences": profile_ops.list_all(
            min_confidence, scope=scope, workspace=workspace)}

    @router.post(f"{PREFIX}/preferences")
    def add_pref(payload: dict = Body(...)) -> dict:
        return profile_ops.upsert(
            kind=str(payload.get("kind") or "other"),
            key=str(payload.get("key") or ""),
            value=str(payload.get("value") or ""),
            confidence=int(payload.get("confidence") or 60),
            scope=str(payload.get("scope") or "global"),
            workspace=str(payload.get("workspace") or ""),
        )

    @router.post(f"{PREFIX}/preferences/{{pref_id}}/scope")
    def set_scope(pref_id: int, payload: dict = Body(...)) -> dict:
        ok = profile_ops.update_scope(
            pref_id,
            str(payload.get("scope") or "global"),
            str(payload.get("workspace") or ""),
        )
        return {"updated": ok}

    @router.delete(f"{PREFIX}/preferences/{{pref_id}}")
    def delete_pref(pref_id: int) -> dict:
        return {"deleted": profile_ops.delete(pref_id)}

    @router.post(f"{PREFIX}/preferences/{{pref_id}}/confidence")
    def set_conf(pref_id: int, payload: dict = Body(...)) -> dict:
        ok = profile_ops.update_confidence(
            pref_id, int(payload.get("confidence") or 50))
        return {"updated": ok}

    @router.post(f"{PREFIX}/extract")
    def extract(payload: dict = Body(...)) -> dict:
        text = str(payload.get("text") or "").strip()
        use_llm = bool(payload.get("use_llm", False))
        if not text:
            return {"candidates": [], "stored": 0}
        candidates = _rule.extract(text)
        if use_llm:
            for c in _llm.extract(text):
                candidates.append(c)
        stored = 0
        results = []
        for c in candidates:
            r = profile_ops.upsert(
                kind=c["kind"], key=c["key"], value=c["value"],
                confidence=c["confidence"])
            results.append({**c, **r})
            stored += 1
        return {"candidates": candidates, "stored": stored,
                "results": results}

    @router.get(f"{PREFIX}/context")
    def context(auto_only: bool = Query(True)) -> dict:
        return {"context": profile_ops.render_context(auto_only=auto_only)}

    @router.post(f"{PREFIX}/rules/import")
    def import_rules(payload: dict = Body(...)) -> dict:
        from backend.agent_learning.rules_importer import import_file
        return import_file(
            str(payload.get("file") or ""),
            workspace=str(payload.get("workspace") or ""),
            scope=str(payload.get("scope") or "project"),
        )

    @router.get(f"{PREFIX}/rules/conflicts")
    def rules_conflicts(workspace: str = Query("")) -> dict:
        from backend.agent_learning.conflict_detector import (
            detect_from_sqlite, summarize,
        )
        return summarize(detect_from_sqlite(workspace=workspace))

    @router.get(f"{PREFIX}/rules/inherit")
    def rules_inherit(workspace: str = Query(...)) -> dict:
        from backend.agent_learning.rule_inheritance import merge_inherited
        return merge_inherited(workspace)

    @router.get(f"{PREFIX}/stats")
    def stats() -> dict:
        all_prefs = profile_ops.list_all(min_confidence=0)
        auto = [p for p in all_prefs if p["auto_applied"]]
        return {"total": len(all_prefs), "auto_applied": len(auto),
                "visible": len([p for p in all_prefs
                                if p["confidence"] >= 30])}

    return router


def build_memory_router() -> Any:
    return build_router()


__all__ = ["build_router", "build_memory_router", "PREFIX"]
