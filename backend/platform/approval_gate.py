"""ApprovalGate: user approval point, wraps frozen ToolApproval."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.platform.proposal import Proposal
from backend.runtime.tools.approval import ToolApproval


class ApprovalGate:
    """Thin adapter over frozen ToolApproval.

    职责：
        - 生成 request_id（proposal_id + user + workspace）
        - 提交提案到 approval queue
        - 查询 / 审批 / 拒绝 / 过期
    """

    VERSION = "1.0"

    def __init__(
        self, approval: Optional[ToolApproval] = None,
    ) -> None:
        self._approval = approval or ToolApproval()

    def request_for_proposal(self, proposal: Proposal) -> str:
        """Create an approval request tied to a proposal id."""
        request_id = self._make_id(proposal)
        if self._approval.get(request_id) is not None:
            return request_id
        self._approval.request(
            request_id=request_id,
            tool_name="code_modify",
            reason=proposal.task[:200],
            risk_level="review",
        )
        return request_id

    def approve(self, proposal: Proposal) -> str:
        rid = self.request_for_proposal(proposal)
        self._approval.approve(rid)
        proposal.transition("approved")
        return rid

    def reject(self, proposal: Proposal) -> str:
        rid = self.request_for_proposal(proposal)
        self._approval.reject(rid)
        proposal.transition("rejected")
        return rid

    def is_approved(self, proposal: Proposal) -> bool:
        return self._approval.approved(self._make_id(proposal))

    def status(self, proposal: Proposal) -> str:
        req = self._approval.get(self._make_id(proposal))
        return req.status if req is not None else "unknown"

    def pending_count(self) -> int:
        return self._approval.count()

    @staticmethod
    def _make_id(proposal: Proposal) -> str:
        return f"apv-{proposal.proposal_id}"

    def ready(self) -> bool:
        return self._approval.ready()

    def dump(self) -> Dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "pending": self.pending_count(),
        }


__all__ = ["ApprovalGate"]
