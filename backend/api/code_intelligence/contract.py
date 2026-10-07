from __future__ import annotations

from typing import Protocol, runtime_checkable

from backend.core.code_intelligence.contracts import (
    CodeIntelligenceRequest,
    CodeIntelligenceResult,
)
from backend.core.protocols.dumpable import DumpableProtocol
from backend.core.protocols.ready import ReadyProtocol


@runtime_checkable
class CodeIntelligenceAPIContract(
    ReadyProtocol,
    DumpableProtocol,
    Protocol,
):
    async def inspect(
        self,
        request: CodeIntelligenceRequest,
    ) -> CodeIntelligenceResult:
        ...


__all__ = ["CodeIntelligenceAPIContract"]
