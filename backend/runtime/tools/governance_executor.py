from __future__ import annotations

from backend.core.tools.argument_contract import ToolArgumentValue
from backend.runtime.tools.approval import ToolApproval
from backend.runtime.tools.permission import ToolPermission
from backend.runtime.tools.policy import ToolPolicy


class GovernanceExecutor:
    """Coordinate policy, permission and approval decisions."""

    VERSION = "7.0"

    def __init__(
        self,
        policy: ToolPolicy,
        permission: ToolPermission,
        approval: ToolApproval,
    ) -> None:
        if policy is None:
            raise ValueError("tool policy required")

        if permission is None:
            raise ValueError("tool permission required")

        if approval is None:
            raise ValueError("tool approval required")

        self.policy = policy
        self.permission = permission
        self.approval = approval

    def evaluate(
        self,
        *,
        tool_name: str,
        role: str = "",
        request_id: str | None = None,
        action: str = "execute",
    ) -> dict[str, ToolArgumentValue]:
        if not tool_name.strip():
            raise ValueError("tool name required")

        policy = self.policy.evaluate(
            tool_name,
            action=action,
        )

        if (
            not policy["allowed"]
            and not policy["requires_approval"]
        ):
            return {
                "allowed": False,
                "stage": "policy",
                "policy": policy,
            }

        permission = self.permission.evaluate(
            role,
            tool_name,
            action,
        )

        if permission["decision"] != "ALLOW":
            return {
                "allowed": False,
                "stage": "permission",
                "policy": policy,
                "permission": permission,
            }

        approval_required = bool(
            policy["requires_approval"]
        )

        approved = (
            not approval_required
            or (
                request_id is not None
                and self.approval.approved(request_id)
            )
        )

        return {
            "allowed": approved,
            "policy": policy,
            "permission": permission,
            "approval_required": approval_required,
            "approved": approved,
        }

    def ready(self) -> bool:
        return (
            self.policy.ready()
            and self.permission.ready()
            and self.approval.ready()
        )

    def dump(
        self,
    ) -> dict[str, ToolArgumentValue]:
        return {
            "name": "GovernanceExecutor",
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "GovernanceExecutor",
]
