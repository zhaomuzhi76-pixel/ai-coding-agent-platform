from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from backend.core.code_intelligence.finding_protocol import (
    CodeFindingProtocol,
)
from backend.core.contracts.value import (
    CoreValue,
)


@dataclass(frozen=True)
class CodeIntelligenceRequest:
    """
    Core-owned stable code intelligence request.
    """

    query: str
    workspace: str = "."
    path: str | None = None
    metadata: dict[str, CoreValue] = field(
        default_factory=dict,
    )

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(self.query, str)
            and bool(self.query.strip())
            and isinstance(self.workspace, str)
            and bool(self.workspace.strip())
            and all(
                isinstance(key, str)
                and _is_core_value(value)
                for key, value in self.metadata.items()
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "query": self.query,
            "workspace": self.workspace,
            "path": self.path,
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


@dataclass(frozen=True)
class CodeIntelligenceResult:
    """
    Core-owned stable code intelligence result.

    Findings remain domain objects behind CodeFindingProtocol.
    """

    findings: tuple[CodeFindingProtocol, ...]
    metadata: dict[str, CoreValue] = field(
        default_factory=dict,
    )

    def ready(
        self,
    ) -> bool:
        return (
            isinstance(self.findings, tuple)
            and all(
                isinstance(
                    finding,
                    CodeFindingProtocol,
                )
                for finding in self.findings
            )
            and all(
                isinstance(key, str)
                and _is_core_value(value)
                for key, value in self.metadata.items()
            )
        )

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        return {
            "name": type(self).__name__,
            "findings": [
                finding.dump()
                for finding in self.findings
            ],
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


@runtime_checkable
class CodeIntelligenceCapabilityProtocol(
    Protocol,
):
    async def inspect(
        self,
        request: CodeIntelligenceRequest,
    ) -> CodeIntelligenceResult:
        ...

    def ready(
        self,
    ) -> bool:
        ...

    def dump(
        self,
    ) -> dict[str, CoreValue]:
        ...


def _is_core_value(
    value: CoreValue,
) -> bool:
    if value is None:
        return True

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return True

    if isinstance(value, list):
        return all(
            _is_core_value(item)
            for item in value
        )

    if isinstance(value, dict):
        return all(
            isinstance(key, str)
            and _is_core_value(item)
            for key, item in value.items()
        )

    return False


__all__ = [
    "CodeIntelligenceCapabilityProtocol",
    "CodeIntelligenceRequest",
    "CodeIntelligenceResult",
]
