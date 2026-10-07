"""L23 无痕测试：全程 /dev/shm，不落盘，不退出终端。"""
from __future__ import annotations

import gc
import shutil
import tempfile
from pathlib import Path

from backend.rag.ingest.review.tools.layer_registry import LAYER_NAMES


def run_ephemeral(layers: list[str] | None) -> dict:
    targets = layers or list(LAYER_NAMES)
    tmp = Path(tempfile.mkdtemp(prefix="l23-", dir="/dev/shm"))
    results: dict = {}
    try:
        for name in targets:
            results[name] = _check(name, tmp)
        results["adapters"] = _adapters()
        results["reranker_selection"] = _reranker_selection()
        results["reranker_center"] = _reranker_center()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        gc.collect()
    ok = all(r.get("ok", False) for r in results.values())
    return {"ok": ok, "tmpfs": str(tmp), "layers": results}


def _check(name: str, tmp: Path) -> dict:
    fn = _CHECKS.get(name)
    if fn is None:
        return {"ok": True, "skipped": True}
    try:
        return fn(tmp)
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _foundation(_tmp: Path) -> dict:
    from backend.rag.ingest.review.foundation.draft_status import (
        ALLOWED_TRANSITIONS, DraftStatus,
    )
    terminal = DraftStatus.DONE.is_terminal and DraftStatus.REJECTED.is_terminal
    no_self = all(s not in dst for s, dst in ALLOWED_TRANSITIONS.items())
    return {"ok": terminal and no_self}


def _storage(_tmp: Path) -> dict:
    from backend.rag.ingest.review.foundation.review_contract import DraftChunk
    from backend.rag.ingest.review.storage.draft_store import InMemoryDraftStore
    store = InMemoryDraftStore()
    store.create_job("t1", [DraftChunk("c1", "t1", "hello")])
    return {"ok": len(store.get_chunks("t1")) == 1}


def _review(_tmp: Path) -> dict:
    from backend.rag.ingest.review.foundation.draft_status import DraftStatus
    from backend.rag.ingest.review.foundation.review_errors import (
        StateTransitionError,
    )
    from backend.rag.ingest.review.review.draft_state_machine import (
        DraftStateMachine,
    )
    m = DraftStateMachine()
    m.register("t1")
    try:
        m.transition("t1", DraftStatus.DONE)
        return {"ok": False, "reason": "illegal_transition_not_rejected"}
    except StateTransitionError:
        return {"ok": True}


def _orchestration(_tmp: Path) -> dict:
    from backend.rag.ingest.review.orchestration.dify_human_input_adapter import (
        export_workflow,
    )
    types = {n["type"] for n in export_workflow()["nodes"]}
    return {"ok": "human_input" in types}


def _api(_tmp: Path) -> dict:
    from backend.rag.ingest.review.api.review_router_factory import build_review_api
    return {"ok": build_review_api() is not None}


def _adapters() -> dict:
    from backend.rag.ingest.review.api.review_factory_production import backends
    report = backends()
    ok = all(isinstance(v, str) for v in report.values())
    return {"ok": ok, "backends": report}


def _reranker_selection() -> dict:
    from backend.rag.ingest.review.api.reranker_router import RerankerApi
    from backend.rag.ingest.review.foundation.reranker_model_spec import (
        build_default_spec,
    )
    from backend.rag.ingest.review.foundation.reranker_model_status import (
        ProbeOutcome,
    )
    from backend.rag.ingest.review.storage.reranker_catalog import RerankerCatalog
    catalog = RerankerCatalog()
    spec = build_default_spec()
    catalog.register(spec)
    api = RerankerApi(catalog)
    initial = api.list_available()
    catalog.mark_result(spec.model_id, ProbeOutcome.OK, "test", 1.0)
    after = api.list_available()
    select = api.select(spec.model_id)
    ok = (
        initial["selectable"] == []
        and len(after["selectable"]) == 1
        and select["selected"] is True
    )
    return {"ok": ok, "initial_selectable": len(initial["selectable"]),
            "after_selectable": len(after["selectable"]),
            "selected": select["selected"]}


def _reranker_center() -> dict:
    from backend.rag.ingest.review.foundation.reranker_model_spec import (
        build_default_spec,
    )
    from backend.rag.ingest.review.foundation.reranker_model_status import (
        ProbeOutcome,
    )
    from backend.rag.ingest.review.review.reranker_center_view import (
        RerankerCenterView,
    )
    from backend.rag.ingest.review.storage.reranker_catalog import RerankerCatalog
    catalog = RerankerCatalog()
    spec = build_default_spec()
    catalog.register(spec)
    view = RerankerCenterView(catalog)
    before = view.build_selectable()
    catalog.mark_result(spec.model_id, ProbeOutcome.OK, "test", 1.0)
    after = view.build_selectable()
    cards = view.build_cards()
    yaml_text = view.build_yaml()
    ok = (
        before["options"] == []
        and len(after["options"]) == 1
        and after["current"] == spec.model_id
        and cards["passing"] == 1
        and "reranker" in yaml_text
    )
    return {"ok": ok, "before": len(before["options"]),
            "after": len(after["options"]), "passing": cards["passing"]}


_CHECKS = {
    "foundation": _foundation,
    "storage": _storage,
    "review": _review,
    "orchestration": _orchestration,
    "api": _api,
}
