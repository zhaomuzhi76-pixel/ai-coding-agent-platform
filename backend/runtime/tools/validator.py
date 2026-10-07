from __future__ import annotations

from backend.core.tools.argument_contract import (
    ToolArguments,
    ToolArgumentValue,
)
from backend.core.tools.schema import ToolSchema


class ToolValidator:
    """Validate and normalize tool arguments against ToolSchema."""

    VERSION = "2.0"

    def validate(
        self,
        schema: ToolSchema,
        arguments: ToolArguments | None = None,
    ) -> dict[str, ToolArgumentValue]:
        if schema is None:
            raise ValueError("tool schema required")

        data = dict(arguments or {})
        errors: list[str] = []

        for parameter in schema.parameters:
            name = parameter.name

            if name not in data:
                if parameter.required:
                    errors.append(
                        f"missing required parameter: {name}"
                    )
                    continue

                if parameter.default is not None:
                    data[name] = parameter.default

            if name in data:
                error = self._check_type(
                    name,
                    data[name],
                    parameter.parameter_type,
                )

                if error:
                    errors.append(error)

        return {
            "valid": not errors,
            "arguments": data,
            "errors": errors,
        }

    def _check_type(
        self,
        name: str,
        value: ToolArgumentValue,
        expected: str,
    ) -> str | None:
        if expected == "string":
            valid = isinstance(value, str)
        elif expected == "integer":
            valid = (
                isinstance(value, int)
                and not isinstance(value, bool)
            )
        elif expected == "number":
            valid = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )
        elif expected == "boolean":
            valid = isinstance(value, bool)
        elif expected == "object":
            valid = isinstance(value, dict)
        elif expected == "array":
            valid = isinstance(value, list)
        else:
            raise ValueError(
                f"unsupported parameter type: {expected}"
            )

        if valid:
            return None

        return (
            f"invalid type for {name}: "
            f"expected {expected}, "
            f"got {type(value).__name__}"
        )

    def ready(self) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, ToolArgumentValue]:
        return {
            "name": "ToolValidator",
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ToolValidator",
]
