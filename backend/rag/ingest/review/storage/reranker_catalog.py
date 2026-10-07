"""L2 排序模型目录 —— 内存注册表，记录链路测试状态。"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.rag.ingest.review.foundation.reranker_model_spec import (
    RerankerModelSpec,
    build_default_spec,
)
from backend.rag.ingest.review.foundation.reranker_model_status import (
    ModelStatus,
    ProbeOutcome,
)


@dataclass
class ModelRecord:
    spec: RerankerModelSpec
    status: ModelStatus = ModelStatus.UNTESTED
    last_probe_at: str = ""
    last_outcome: ProbeOutcome | None = None
    last_message: str = ""
    last_latency_ms: float = 0.0


class RerankerCatalog:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, ModelRecord] = {}
        self._selected: str = ""

    def register(self, spec: RerankerModelSpec) -> None:
        with self._lock:
            self._records.setdefault(spec.model_id, ModelRecord(spec=spec))

    def unregister(self, model_id: str) -> bool:
        with self._lock:
            return self._records.pop(model_id, None) is not None

    def get(self, model_id: str) -> ModelRecord | None:
        with self._lock:
            return self._records.get(model_id)

    def all_records(self) -> tuple[ModelRecord, ...]:
        with self._lock:
            return tuple(self._records.values())

    def selectable_records(self) -> tuple[ModelRecord, ...]:
        return tuple(r for r in self.all_records() if r.status.selectable)

    def selectable_specs(self) -> tuple[RerankerModelSpec, ...]:
        return tuple(r.spec for r in self.selectable_records())

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

    def disable(self, model_id: str) -> None:
        self._update(model_id, status=ModelStatus.DISABLED)

    def get_selected(self) -> str:
        with self._lock:
            return self._selected

    def set_selected(self, model_id: str) -> bool:
        with self._lock:
            rec = self._records.get(model_id)
            if rec is None or not rec.status.selectable:
                return False
            self._selected = model_id
            return True

    def _update(self, model_id: str, **changes: Any) -> None:
        with self._lock:
            rec = self._records.get(model_id)
            if rec is None:
                return
            for k, v in changes.items():
                if hasattr(rec, k):
                    setattr(rec, k, v)


_default_catalog: RerankerCatalog | None = None
_catalog_lock = threading.Lock()


def get_default_catalog() -> RerankerCatalog:
    global _default_catalog
    with _catalog_lock:
        if _default_catalog is None:
            _default_catalog = RerankerCatalog()
            _default_catalog.register(build_default_spec())
        return _default_catalog
