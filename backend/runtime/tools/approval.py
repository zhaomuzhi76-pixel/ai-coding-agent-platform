from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from backend.core.tools.argument_contract import ToolArgumentValue

ApprovalState = Literal[
    "pending",
    "approved",
    "rejected",
    "expired",
]


@dataclass
class ApprovalRequest:
    request_id: str
    tool_name: str
    reason: str
    risk_level: str
    status: ApprovalState
    created_at: str

    def dump(self) -> dict[str, ToolArgumentValue]:
        return {
            "id": self.request_id,
            "tool": self.tool_name,
            "reason": self.reason,
            "risk": self.risk_level,
            "status": self.status,
            "created_at": self.created_at,
        }


class ToolApproval:
    """Human approval lifecycle for tool execution."""

    VERSION = "3.0"
    TIMEZONE = ZoneInfo("Asia/Shanghai")

    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def request(
        self,
        request_id: str,
        tool_name: str,
        reason: str = "",
        risk_level: str = "safe",
    ) -> None:
        if not request_id.strip():
            raise ValueError("request id required")

        if not tool_name.strip():
            raise ValueError("tool name required")

        if request_id in self._requests:
            raise ValueError(
                f"approval request exists: {request_id}"
            )

        self._requests[request_id] = ApprovalRequest(
            request_id=request_id,
            tool_name=tool_name,
            reason=reason,
            risk_level=risk_level,
            status="pending",
            created_at=datetime.now(
                self.TIMEZONE
            ).isoformat(),
        )

    def approve(
        self,
        request_id: str,
    ) -> None:
        self._update(
            request_id,
            "approved",
        )

    def reject(
        self,
        request_id: str,
    ) -> None:
        self._update(
            request_id,
            "rejected",
        )

    def expire(
        self,
        request_id: str,
    ) -> None:
        self._update(
            request_id,
            "expired",
        )

    def approved(
        self,
        request_id: str,
    ) -> bool:
        request = self._requests.get(request_id)

        return (
            request is not None
            and request.status == "approved"
        )

    def get(
        self,
        request_id: str,
    ) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def count(self) -> int:
        return len(self._requests)

    def clear(self) -> None:
        self._requests.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, ToolArgumentValue]:
        return {
            "name": "ToolApproval",
            "version": self.VERSION,
            "ready": self.ready(),
            "count": self.count(),
        }

    def _update(
        self,
        request_id: str,
        state: ApprovalState,
    ) -> None:
        if not request_id.strip():
            raise ValueError("request id required")

        request = self._requests.get(request_id)

        if request is None:
            raise KeyError(request_id)

        request.status = state


__all__ = [
    "ApprovalRequest",
    "ApprovalState",
    "ToolApproval",
]
