from __future__ import annotations

from typing import Literal

from backend.core.tools.argument_contract import ToolArgumentValue

ToolRiskLevel = Literal["safe", "review", "dangerous"]
ToolPolicyDecision = Literal[
    "ALLOW",
    "REQUIRE_APPROVAL",
    "DENY",
]


class ToolPolicy:
    """Tool risk policy evaluation."""

    VERSION = "3.0"
    DEFAULT_LEVEL: ToolRiskLevel = "safe"

    def __init__(self) -> None:
        self._rules: dict[str, ToolRiskLevel] = {}

    def set_level(
        self,
        tool_name: str,
        level: ToolRiskLevel,
    ) -> None:
        self._validate_name(tool_name)

        if level not in ("safe", "review", "dangerous"):
            raise ValueError(f"unsupported risk level: {level}")

        self._rules[tool_name] = level

    def level(self, tool_name: str) -> ToolRiskLevel:
        self._validate_name(tool_name)

        return self._rules.get(
            tool_name,
            self.DEFAULT_LEVEL,
        )

    def evaluate(
        self,
        tool_name: str,
        *,
        action: str | None = None,
        resource: str | None = None,
    ) -> dict[str, ToolArgumentValue]:
        risk_level = self.level(tool_name)
        decision = self._decision(risk_level)

        return {
            "tool": tool_name,
            "action": action,
            "resource": resource,
            "risk_level": risk_level,
            "decision": decision,
            "allowed": decision == "ALLOW",
            "requires_approval": decision == "REQUIRE_APPROVAL",
            "reason": self._reason(decision),
        }

    def is_allowed(self, tool_name: str) -> bool:
        return self.evaluate(
            tool_name
        )["decision"] == "ALLOW"

    def requires_approval(self, tool_name: str) -> bool:
        return (
            self.evaluate(tool_name)["decision"]
            == "REQUIRE_APPROVAL"
        )

    def remove(self, tool_name: str) -> None:
        self._validate_name(tool_name)
        self._rules.pop(tool_name, None)

    def clear(self) -> None:
        self._rules.clear()

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, ToolArgumentValue]:
        return {
            "name": "ToolPolicy",
            "version": self.VERSION,
            "ready": self.ready(),
            "rules": dict(self._rules),
        }

    def _decision(
        self,
        level: ToolRiskLevel,
    ) -> ToolPolicyDecision:
        if level == "safe":
            return "ALLOW"

        if level == "review":
            return "REQUIRE_APPROVAL"

        return "DENY"

    def _reason(
        self,
        decision: ToolPolicyDecision,
    ) -> str:
        return {
            "ALLOW": "tool classified as safe",
            "REQUIRE_APPROVAL": "tool requires human approval",
            "DENY": "tool execution denied by policy",
        }[decision]

    def _validate_name(
        self,
        tool_name: str,
    ) -> None:
        if not isinstance(tool_name, str):
            raise TypeError("tool_name must be str")

        if not tool_name.strip():
            raise ValueError("tool_name required")


__all__ = [
    "ToolPolicy",
    "ToolPolicyDecision",
    "ToolRiskLevel",
]
