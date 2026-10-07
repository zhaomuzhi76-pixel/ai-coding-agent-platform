"""AI coding platform facade layer.

职责边界：
    code_intelligence.*     -> 修改工作流（冻结）
    agent.orchestration.*   -> Planner/Coder/Reviewer 编排（冻结）
    runtime.tools.*         -> 工具运行时（冻结）
    observability.*         -> tracer/alert/report（新增）
    code_intelligence.memory.* -> 三层记忆（冻结）
    platform.*              -> 只做统一门面 + 会话 + 审批 + 桥接
"""
from backend.platform.session import SessionTurn, CodingSession
from backend.platform.request import CodingRequest
from backend.platform.proposal import (
    Proposal,
    STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED,
    STATUS_APPLIED, STATUS_FAILED, STATUS_ROLLED_BACK,
)
from backend.platform.approval_gate import ApprovalGate
from backend.platform.event_bridge import EventBridge
from backend.platform.memory_bridge import MemoryBridge
from backend.platform.pipeline import PlatformPipeline
from backend.platform.platform import CodingPlatform
from backend.platform.api_contract import (
    ApiResponse, ApiError,
    EP_CREATE_SESSION, EP_PROPOSE, EP_APPROVE, EP_REJECT,
    EP_APPLY, EP_VERIFY, EP_LEARN,
    ALL_ENDPOINTS,
)

__all__ = [
    "SessionTurn", "CodingSession",
    "CodingRequest",
    "Proposal",
    "STATUS_PENDING", "STATUS_APPROVED", "STATUS_REJECTED",
    "STATUS_APPLIED", "STATUS_FAILED", "STATUS_ROLLED_BACK",
    "ApprovalGate",
    "EventBridge", "MemoryBridge",
    "PlatformPipeline", "CodingPlatform",
    "ApiResponse", "ApiError",
    "EP_CREATE_SESSION", "EP_PROPOSE", "EP_APPROVE", "EP_REJECT",
    "EP_APPLY", "EP_VERIFY", "EP_LEARN",
    "ALL_ENDPOINTS",
]
