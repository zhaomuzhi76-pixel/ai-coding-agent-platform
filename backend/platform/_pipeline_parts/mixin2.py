"""Mixin 2 of PlatformPipeline."""
from __future__ import annotations
from .part1 import (Any, CodingSession, Dict, Optional, Proposal, emit_event, read_primary,)  # noqa: F401
class _Mixin2:
    def reject(
        self, session: CodingSession, proposal: Proposal,
        reason: str = "",
    ) -> None:
        self._gate.reject(proposal)
        self._memory.on_reject(
            task=proposal.task, plan=proposal.plan,
            changes=proposal.changes,
            workspace=proposal.metadata.get("workspace", ""),
            feedback=reason,
        )
        session.add_turn(
            "user", f"rejected {proposal.proposal_id}: {reason}",
            proposal_id=proposal.proposal_id,
        )

    @staticmethod
    async def _emit(self, event_callback: Any, event: Any) -> None:
        await emit_event(self._events, event_callback, event)

    @staticmethod
    def _read_primary(
        workspace: str, rel_path: str, *, allow_missing: bool = False,
    ) -> str:
        return read_primary(
            workspace, rel_path, allow_missing=allow_missing,
        )

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        return self._proposals.get(proposal_id)

    def apply_proposal(
        self, proposal_id: str,
        on_step: Any = None,
    ) -> Dict[str, Any]:
        """简化入口：按 proposal_id 直接 apply（session 可选）。"""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(f"proposal not found: {proposal_id}")
        try:
            from backend.platform.session import CodingSession
            session = CodingSession()
        except Exception:
            session = None
        return self.apply(session, proposal, on_step=on_step)

    def ready(self) -> bool:
        return (
            bool(self._orchestrator.ready())
            and self._gate.ready()
            and self._events.ready()
            and self._memory.ready()
        )

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "proposals": self.proposal_count,
            "applied": self.applied_count,
            "gate": self._gate.dump(),
            "events": self._events.dump(),
            "memory": self._memory.dump(),
        }
