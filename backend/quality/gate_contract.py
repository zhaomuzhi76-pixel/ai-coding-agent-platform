"""质量门禁契约。所有门禁实现必须遵循本契约，禁止副作用。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class GateViolation:
    code: str
    message: str
    location: str = ""
    severity: str = "error"  # error | warning


@dataclass(frozen=True)
class GateContext:
    root: str
    layer: str = ""
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    violations: Sequence[GateViolation] = ()
    metrics: Mapping[str, Any] = field(default_factory=dict)


class Gate(Protocol):
    name: str
    layer: str

    def run(self, ctx: GateContext) -> GateResult: ...
