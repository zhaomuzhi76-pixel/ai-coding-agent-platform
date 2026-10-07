from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.core.contracts.payload import Payload


@dataclass(frozen=True)
class KernelOutputPayload:
    value: Any

    def dump(self) -> Payload:
        return {"value": self.normalize(self.value)}

    @classmethod
    def normalize(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, dict):
            return {
                str(key): cls.normalize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [cls.normalize(item) for item in value]

        return str(value)


__all__ = ["KernelOutputPayload"]
