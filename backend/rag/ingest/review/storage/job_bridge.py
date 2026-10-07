"""L2 job bridge —— L23 草稿桥接到现有 rag.ingest.jobs 系统。

用 inspect.signature 智能调用，匹配现有 JobRegistry.create/update/finish。
"""
from __future__ import annotations

import importlib
import inspect
from typing import Any

from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.foundation.review_contract import DraftChunk

_MODULE = "backend.rag.ingest.jobs.registry"
_FACTORY_NAMES = (
    "get_default_job_registry", "get_registry",
    "get_default_registry", "registry",
)
_CREATE_NAMES = ("create", "register", "create_job", "new_job", "add")
_UPDATE_NAMES = ("update", "update_status", "update_progress",
                 "set_status", "mark", "transition", "append_step")
_FINISH_NAMES = ("finish", "complete", "done", "close")
_TERMINAL = frozenset({DraftStatus.DONE.value, DraftStatus.REJECTED.value})


class DraftJobBridge:
    """把 L23 草稿状态镜像到现有 job 系统。"""

    def __init__(self, registry: Any | None = None) -> None:
        self._registry = registry if registry is not None else _load_registry()

    @property
    def backend(self) -> str:
        return "real" if self._registry is not None else "fallback"

    def on_draft_created(self, job_id: str, chunks: list[DraftChunk]) -> None:
        payload = {
            "stage": "draft",
            "status": DraftStatus.PENDING_REVIEW.value,
            "chunk_count": len(chunks),
            "chunks": [c.chunk_id for c in chunks][:64],
        }
        _try_call_chain(self._registry, _CREATE_NAMES, job_id, payload)

    def on_transition(self, job_id: str,
                      src: DraftStatus, dst: DraftStatus) -> None:
        payload = {
            "status": dst.value,
            "from": src.value,
            "stage": "review",
        }
        names = _FINISH_NAMES if dst.value in _TERMINAL else _UPDATE_NAMES
        if not _try_call_chain(self._registry, names, job_id, payload):
            # 终态兜底：再尝试 update 系列
            if dst.value in _TERMINAL:
                _try_call_chain(self._registry, _UPDATE_NAMES, job_id, payload)


def _try_call_chain(registry: Any, names: tuple[str, ...],
                    job_id: str, payload: dict) -> bool:
    if registry is None:
        return False
    for name in names:
        fn = getattr(registry, name, None)
        if not callable(fn):
            continue
        ok, _ = _smart_call(fn, job_id, payload)
        if ok:
            return True
    return False


def _smart_call(fn: Any, job_id: str, payload: dict) -> tuple[bool, str]:
    """按 fn 签名智能匹配 job_id / payload 命名参数。"""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return False, "no_signature"
    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        value = _match(name, job_id, payload)
        if value is _MISS:
            if param.default is inspect.Parameter.empty:
                return False, f"missing:{name}"
            continue
        kwargs[name] = value
    try:
        fn(**kwargs)
        return True, "ok"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


_MISS = object()

_JOB_ID_NAMES = frozenset({
    "job_id", "id", "jid", "job", "record_id", "task_id",
})
_PAYLOAD_NAMES = frozenset({
    "payload", "data", "record", "manifest", "meta", "metadata",
    "info", "detail", "update", "patch", "changes", "body",
})
_STATUS_NAMES = frozenset({"status", "state", "new_status", "phase"})
_PROGRESS_NAMES = frozenset({"progress", "pct", "percent"})


def _match(name: str, job_id: str, payload: dict) -> Any:
    n = name.lower()
    if n in _JOB_ID_NAMES:
        return job_id
    if n in _PAYLOAD_NAMES:
        return payload
    if n in _STATUS_NAMES:
        return payload.get("status")
    if n in _PROGRESS_NAMES:
        return 0.0
    return _MISS


def _load_registry() -> Any | None:
    try:
        mod = importlib.import_module(_MODULE)
    except Exception:
        return None
    for name in _FACTORY_NAMES:
        obj = getattr(mod, name, None)
        if callable(obj):
            try:
                instance = obj()
                if instance is not None:
                    return instance
            except Exception:
                continue
        elif obj is not None:
            return obj
    return None


def build_bridge(registry: Any | None = None) -> DraftJobBridge:
    return DraftJobBridge(registry)
