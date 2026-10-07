from __future__ import annotations

from backend.runtime.tools.policy import ToolPolicy


class ToolSecurityProfile:
    """
    Canonical builtin tool security profile.

    Owns:
        - builtin tool risk classification

    Does not own:
        - permission evaluation
        - approval state
        - tool execution
    """

    VERSION = "1.0"

    SAFE_TOOLS = (
        "file_read",
        "search",
        "file_tree",
        "workspace_scan",
        "code_analysis",
    )

    REVIEW_TOOLS = (
        "file_write",
        "file_edit",
        "terminal",
    )

    def configure(self, policy: ToolPolicy) -> None:
        if not isinstance(policy, ToolPolicy):
            raise TypeError("policy must ToolPolicy")
        for name in self.SAFE_TOOLS:
            policy.set_level(name, "safe")
        for name in self.REVIEW_TOOLS:
            policy.set_level(name, "review")

    def ready(self) -> bool:
        return bool(self.SAFE_TOOLS and self.REVIEW_TOOLS)

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "safe_tools": self.SAFE_TOOLS,
            "review_tools": self.REVIEW_TOOLS,
            "ready": self.ready(),
        }


__all__ = ["ToolSecurityProfile"]
