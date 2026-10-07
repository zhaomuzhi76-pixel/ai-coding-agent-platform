"""provider_center 目录 —— 多 kind 通用注册表。"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.rag.ingest.review.provider_center.spec import (
    ModelStatus,
    ProbeOutcome,
    ProviderSpec,
    SUPPORTED_KINDS,
)


@dataclass
class ProviderRecord:
    spec: ProviderSpec
    status: ModelStatus = ModelStatus.UNTESTED
    last_probe_at: str = ""
    last_outcome: ProbeOutcome | None = None
    last_message: str = ""
    last_latency_ms: float = 0.0


class ProviderCatalog:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, ProviderRecord] = {}
        self._selected: dict[str, str] = {}

    def register(self, spec: ProviderSpec) -> None:
        if spec.kind not in SUPPORTED_KINDS:
            return
        with self._lock:
            self._records.setdefault(spec.model_id, ProviderRecord(spec=spec))

    def unregister(self, model_id: str) -> bool:
        with self._lock:
            rec = self._records.pop(model_id, None)
            if rec is None:
                return False
            for kind, mid in list(self._selected.items()):
                if mid == model_id:
                    self._selected.pop(kind, None)
            return True

    def get(self, model_id: str) -> ProviderRecord | None:
        with self._lock:
            return self._records.get(model_id)

    def by_kind(self, kind: str) -> tuple[ProviderRecord, ...]:
        with self._lock:
            return tuple(r for r in self._records.values()
                         if r.spec.kind == kind)

    def selectable(self, kind: str) -> tuple[ProviderRecord, ...]:
        return tuple(r for r in self.by_kind(kind) if r.status.selectable)

    def mark_probing(self, model_id: str) -> None:
        self._update(model_id, status=ModelStatus.PROBING)

    def mark_result(self, model_id: str, outcome: ProbeOutcome,
                    message: str = "", latency_ms: float = 0.0) -> None:
        status = ModelStatus.PASSING if outcome is ProbeOutcome.OK \
            else ModelStatus.FAILING
        self._update(model_id, status=status,
                     last_probe_at=datetime.now(timezone.utc).isoformat(),
                     last_outcome=outcome,
                     last_message=message, last_latency_ms=latency_ms)

    def get_selected(self, kind: str) -> str:
        with self._lock:
            return self._selected.get(kind, "")

    def set_selected(self, kind: str, model_id: str) -> bool:
        with self._lock:
            rec = self._records.get(model_id)
            if rec is None or rec.spec.kind != kind:
                return False
            if not rec.status.selectable:
                return False
            self._selected[kind] = model_id
            return True

    def _update(self, model_id: str, **changes: Any) -> None:
        with self._lock:
            rec = self._records.get(model_id)
            if rec is None:
                return
            for k, v in changes.items():
                if hasattr(rec, k):
                    setattr(rec, k, v)


_default: ProviderCatalog | None = None
_lock = threading.Lock()


def get_default_catalog() -> ProviderCatalog:
    global _default
    with _lock:
        if _default is None:
            _default = ProviderCatalog()
        return _default
