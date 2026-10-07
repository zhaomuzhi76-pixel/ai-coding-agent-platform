from __future__ import annotations

from typing import Literal

from backend.core.tools.argument_contract import ToolArgumentValue

ToolPermissionDecision = Literal["ALLOW", "DENY"]


class ToolPermission:
    """Role-based tool permission boundary."""

    VERSION = "4.0"

    def __init__(self) -> None:
        self._rules: dict[str, dict[str, frozenset[str]]] = {}

    def grant(
        self,
        role: str,
        tool_name: str,
        actions: list[str] | None = None,
    ) -> None:
        self._validate(role, tool_name)

        granted = frozenset(
            actions if actions is not None else ["execute"]
        )

        if not granted or any(not item.strip() for item in granted):
            raise ValueError("valid actions required")

        self._rules.setdefault(role, {})[tool_name] = granted

    def revoke(
        self,
        role: str,
        tool_name: str,
    ) -> None:
        self._validate(role, tool_name)

        role_rules = self._rules.get(role)

        if role_rules is None:
            return

        role_rules.pop(tool_name, None)

        if not role_rules:
            self._rules.pop(role, None)

    def evaluate(
        self,
        role: str,
        tool_name: str,
        action: str = "execute",
    ) -> dict[str, ToolArgumentValue]:
        self._validate(role, tool_name)

        if not action.strip():
            raise ValueError("action required")

        actions = self._rules.get(role, {}).get(tool_name)

        if actions is None:
            return {
                "decision": "DENY",
                "reason": "permission_missing",
            }

        if action not in actions:
            return {
                "decision": "DENY",
                "reason": "action_denied",
            }

        return {
            "decision": "ALLOW",
            "role": role,
            "tool": tool_name,
            "action": action,
        }

    def allowed(
        self,
        role: str,
        tool_name: str,
        action: str = "execute",
    ) -> bool:
        return self.evaluate(
            role,
            tool_name,
            action,
        )["decision"] == "ALLOW"

    def require(
        self,
        role: str,
        tool_name: str,
        action: str = "execute",
    ) -> None:
        if not self.allowed(role, tool_name, action):
            raise PermissionError(
                f"permission denied: {tool_name}"
            )

    def roles(self) -> list[str]:
        return list(self._rules)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, ToolArgumentValue]:
        return {
            "name": "ToolPermission",
            "version": self.VERSION,
            "ready": self.ready(),
            "roles": len(self._rules),
        }

    def _validate(
        self,
        role: str,
        tool_name: str,
    ) -> None:
        if not role.strip():
            raise ValueError("role required")
        if not tool_name.strip():
            raise ValueError("tool name required")


__all__ = [
    "ToolPermission",
    "ToolPermissionDecision",
]
