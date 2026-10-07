from __future__ import annotations

from backend.runtime.tools.approval import ToolApproval
from backend.runtime.tools.governance_executor import GovernanceExecutor
from backend.runtime.tools.permission import ToolPermission
from backend.runtime.tools.policy import ToolPolicy
from backend.runtime.tools.security.profile import ToolSecurityProfile


class ToolSecurityComposition:
    """
    Canonical construction owner for builtin tool governance.
    """

    VERSION = "2.0"

    def __init__(
        self,
        profile: ToolSecurityProfile | None = None,
    ) -> None:
        self.profile = profile or ToolSecurityProfile()

    def create(self) -> GovernanceExecutor:
        if not self.ready():
            raise RuntimeError("tool security profile unavailable")

        policy = ToolPolicy()
        self.profile.configure(policy)

        governance = GovernanceExecutor(
            policy=policy,
            permission=ToolPermission(),
            approval=ToolApproval(),
        )

        if not governance.ready():
            raise RuntimeError("tool governance unavailable")

        return governance

    def ready(self) -> bool:
        return self.profile.ready()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "profile": self.profile.dump(),
            "ready": self.ready(),
        }


__all__ = ["ToolSecurityComposition"]
