"""CodingPlatform: top-level facade for AI coding platform."""
from __future__ import annotations

from typing import Any, Dict, Optional

from backend.platform.approval_gate import ApprovalGate
from backend.platform.event_bridge import EventBridge
from backend.platform.memory_bridge import MemoryBridge
from backend.platform.pipeline import PlatformPipeline
from backend.platform.proposal import Proposal
from backend.platform.request import CodingRequest
from backend.platform.session import CodingSession


class CodingPlatform:
    """One-stop platform: sessions + pipeline + observability + i18n."""

    VERSION = "1.0"

    def __init__(
        self,
        pipeline: PlatformPipeline,
        *,
        translator: Optional[Any] = None,
    ) -> None:
        self._pipeline = pipeline
        self._translator = translator
        self._sessions: Dict[str, CodingSession] = {}
        self._proposals: Dict[str, Proposal] = {}

    # ─── session lifecycle ──────────────────────────────────
    def create_session(
        self,
        *,
        workspace: str,
        user_id: str = "",
        locale: str = "zh-CN",
        model: str = "",
    ) -> CodingSession:
        s = CodingSession(
            workspace=workspace,
            user_id=user_id,
            locale=locale,
            model=model,
        )
        self._sessions[s.session_id] = s
        return s

    def get_session(self, session_id: str) -> CodingSession:
        if session_id not in self._sessions:
            raise KeyError(f"session not found: {session_id}")
        return self._sessions[session_id]

    def sessions(self) -> list:
        return list(self._sessions.keys())

    # ─── pipeline access ────────────────────────────────────
    async def propose(
        self,
        session_id: str,
        request: CodingRequest,
        *,
        gateway: Any = None,
        router: Any = None,
    ) -> Proposal:
        session = self.get_session(session_id)
        proposal = await self._pipeline.propose(
            session, request,
            gateway=gateway, router=router,
        )
        self._proposals[proposal.proposal_id] = proposal
        return proposal

    def approve(self, session_id: str, proposal_id: str) -> None:
        session = self.get_session(session_id)
        proposal = self._get_proposal(proposal_id)
        self._pipeline.approve(session, proposal)

    def reject(
        self, session_id: str, proposal_id: str, reason: str = "",
    ) -> None:
        session = self.get_session(session_id)
        proposal = self._get_proposal(proposal_id)
        self._pipeline.reject(session, proposal, reason)

    def apply(
        self, session_id: str, proposal_id: str,
    ) -> Dict[str, Any]:
        session = self.get_session(session_id)
        proposal = self._get_proposal(proposal_id)
        return self._pipeline.apply(session, proposal)

    def verify(
        self, session_id: str, proposal_id: str, workspace: str = "",
    ) -> Dict[str, Any]:
        session = self.get_session(session_id)
        proposal = self._get_proposal(proposal_id)
        return self._pipeline.verify(session, proposal, workspace)

    def learn(self, session_id: str, proposal_id: str) -> None:
        session = self.get_session(session_id)
        proposal = self._get_proposal(proposal_id)
        self._pipeline.learn(session, proposal)

    def get_proposal(self, proposal_id: str) -> Proposal:
        """转发：拿到 proposal（供 binding.apply_adapter 用）。"""
        return self._get_proposal(proposal_id)

    def apply_proposal(
        self, proposal_id: str, on_step: Any = None,
    ) -> Dict[str, Any]:
        """转发：按 proposal_id 直接 apply（无 session 上下文）。

        与 CodingPlatform.apply(session_id, proposal_id) 的区别：
            - apply          需 session_id（用户会话上下文）
            - apply_proposal 无 session（后台任务/pipeline 内部用）
        """
        return self._pipeline.apply_proposal(proposal_id, on_step=on_step)

    # ─── i18n (optional) ────────────────────────────────────
    def translate(
        self, key: str, locale: Optional[str] = None, **params: Any,
    ) -> str:
        if self._translator is None:
            return key
        return self._translator.translate(key, locale=locale, **params)

    # ─── introspection ──────────────────────────────────────
    def _get_proposal(self, proposal_id: str) -> Proposal:
        if proposal_id not in self._proposals:
            raise KeyError(f"proposal not found: {proposal_id}")
        return self._proposals[proposal_id]

    def proposal(self, proposal_id: str) -> Proposal:
        return self._get_proposal(proposal_id)

    def proposals(self) -> list:
        return list(self._proposals.keys())

    def ready(self) -> bool:
        return self._pipeline.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "sessions": len(self._sessions),
            "proposals": len(self._proposals),
            "pipeline": self._pipeline.dump(),
            "has_translator": self._translator is not None,
        }


__all__ = ["CodingPlatform"]
