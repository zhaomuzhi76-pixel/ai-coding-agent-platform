"""API contract for frontend integration (request / response)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ApiError:
    code: str
    message: str
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.detail:
            out["detail"] = self.detail
        return out


@dataclass
class ApiResponse:
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[ApiError] = None

    @classmethod
    def success(cls, data: Dict[str, Any]) -> "ApiResponse":
        return cls(ok=True, data=dict(data))

    @classmethod
    def failure(cls, code: str, message: str,
                detail: Optional[str] = None) -> "ApiResponse":
        return cls(ok=False, error=ApiError(code=code,
                                            message=message, detail=detail))

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"ok": self.ok}
        if self.data is not None:
            out["data"] = dict(self.data)
        if self.error is not None:
            out["error"] = self.error.to_dict()
        return out


# ─── Endpoint names (frozen contract for frontend) ────────
EP_CREATE_SESSION = "platform.session.create"
EP_GET_SESSION = "platform.session.get"
EP_PROPOSE = "platform.propose"
EP_APPROVE = "platform.approve"
EP_REJECT = "platform.reject"
EP_APPLY = "platform.apply"
EP_VERIFY = "platform.verify"
EP_LEARN = "platform.learn"
EP_LIST_MODELS = "platform.models.list"
EP_LIST_DOMAINS = "platform.domains.list"

ALL_ENDPOINTS = (
    EP_CREATE_SESSION, EP_GET_SESSION,
    EP_PROPOSE, EP_APPROVE, EP_REJECT,
    EP_APPLY, EP_VERIFY, EP_LEARN,
    EP_LIST_MODELS, EP_LIST_DOMAINS,
)


@dataclass
class CreateSessionPayload:
    workspace: str
    user_id: str = ""
    locale: str = "zh-CN"
    model: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace": self.workspace,
            "user_id": self.user_id,
            "locale": self.locale,
            "model": self.model,
        }


@dataclass
class ProposePayload:
    session_id: str
    task: str
    files: List[str]
    model: str
    locale: str = "zh-CN"
    user_id: str = ""
    instruction: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "task": self.task,
            "files": list(self.files),
            "model": self.model,
            "locale": self.locale,
            "user_id": self.user_id,
            "instruction": self.instruction,
            "metadata": dict(self.metadata),
        }


@dataclass
class ApprovePayload:
    session_id: str
    proposal_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "proposal_id": self.proposal_id,
        }


@dataclass
class RejectPayload:
    session_id: str
    proposal_id: str
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "proposal_id": self.proposal_id,
            "reason": self.reason,
        }


__all__ = [
    "ApiError", "ApiResponse",
    "EP_CREATE_SESSION", "EP_GET_SESSION",
    "EP_PROPOSE", "EP_APPROVE", "EP_REJECT",
    "EP_APPLY", "EP_VERIFY", "EP_LEARN",
    "EP_LIST_MODELS", "EP_LIST_DOMAINS",
    "ALL_ENDPOINTS",
    "CreateSessionPayload", "ProposePayload",
    "ApprovePayload", "RejectPayload",
]
