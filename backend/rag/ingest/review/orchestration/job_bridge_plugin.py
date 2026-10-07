"""L4 job bridge 插件 —— 挂载草稿与现有 job 系统的桥接。"""
from __future__ import annotations

from typing import Any

from backend.rag.ingest.review.foundation.draft_status import DraftStatus
from backend.rag.ingest.review.review.draft_state_machine import (
    DraftStateMachine,
)
from backend.rag.ingest.review.storage.draft_store import (
    get_default_draft_store,
)
from backend.rag.ingest.review.storage.job_bridge import build_bridge


class JobBridgePlugin:
    descriptor = {
        "name": "rag_review_job_bridge",
        "version": "1.0.0",
        "description": "L23 草稿状态桥接到现有 rag.ingest.jobs 系统",
        "capabilities": ("mirror_draft_created", "mirror_transition"),
    }

    @property
    def name(self) -> str:
        return self.descriptor["name"]

    def __init__(self) -> None:
        self._bridge = build_bridge()

    def backend(self) -> str:
        return self._bridge.backend

    def attach_to(self, machine: DraftStateMachine) -> None:
        """给状态机挂一个 listener，自动镜像到 job 系统。"""
        machine.add_listener(self._on_transition)

    def notify_draft_created(self, job_id: str) -> None:
        store = get_default_draft_store()
        try:
            chunks = list(store.get_chunks(job_id))
        except Exception:
            chunks = []
        self._bridge.on_draft_created(job_id, chunks)

    def _on_transition(self, job_id: str,
                       src: DraftStatus, dst: DraftStatus) -> None:
        self._bridge.on_transition(job_id, src, dst)

    def on_load(self, context: dict | None = None) -> None:
        return None

    def on_unload(self) -> None:
        return None


def build_plugin() -> JobBridgePlugin:
    return JobBridgePlugin()
