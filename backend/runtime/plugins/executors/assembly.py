from __future__ import annotations

from typing import Any

from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)
from backend.core.execution.llm_execution_contract import (
    LLMExecutionProviderProtocol,
)
from backend.runtime.execution.execution_contracts import (
    ExecutorResolverProtocol,
)
from backend.runtime.executors.code_modify_executor import (
    CodeModifyExecutor,
)
from backend.runtime.executors.multi_file_modify_executor import (
    MultiFileModifyExecutor,
)
from backend.runtime.executors.project_analysis_executor import (
    ProjectAnalysisExecutor,
)
from backend.runtime.executors.error_fix_executor import (
    ErrorFixExecutor,
)
from backend.runtime.executors.executor_contract_registry import (
    ExecutorContractRegistry,
)
from backend.runtime.executors.executor_resolver import (
    ExecutorResolver,
)
from backend.runtime.executors.llm_executor import (
    LLMExecutor,
)
from backend.runtime.executors.registry import (
    ExecutorRegistry,
)
from backend.runtime.executors.summary_executor import (
    SummaryExecutor,
)
from backend.runtime.executors.tool_executor import (
    ToolExecutor,
)
from backend.runtime.executors.tool_execution_port import (
    ToolExecutionPort,
)


class RuntimeExecutorAssembly:
    """
    Runtime executor assembly boundary.

    Tool execution enters through ToolExecutionPort.
    """

    VERSION = "2.0"

    CONTRACTS = {
        "llm": "llm",
        "file_read": "tool_executor",
        "file_write": "tool_executor",
        "workspace_scan": "tool_executor",
        "terminal": "tool_executor",
        "testing": "tool_executor",
        "code_analysis": "tool_executor",
        "code_modify": "code_modify",
        "multi_file_modify": "multi_file_modify",
        "project_analysis": "project_analysis",
        "fix_error": "fix_error",
        "summary": "summary",
    }

    def __init__(
        self,
        *,
        llm_provider: LLMExecutionProviderProtocol,
        tools: ToolExecutionPort,
        modification: CodeModificationProviderProtocol,
    ) -> None:
        self._validate(
            llm_provider=llm_provider,
            tools=tools,
            modification=modification,
        )

        self.llm_provider = llm_provider
        self.tools = tools
        self.modification = modification
        self.registry = ExecutorRegistry()
        self.contract_registry = (
            ExecutorContractRegistry()
        )
        self.resolver: ExecutorResolverProtocol | None = None

    def assemble(
        self,
    ) -> ExecutorResolverProtocol:
        if self.resolver is not None:
            return self.resolver

        self.registry.register(
            "llm",
            LLMExecutor(
                provider=self.llm_provider,
            ),
        )
        self.registry.register(
            "tool_executor",
            ToolExecutor(
                execution_port=self.tools,
            ),
        )
        self.registry.register(
            "code_modify",
            CodeModifyExecutor(
                provider=self.modification,
            ),
        )
        self.registry.register(
            "multi_file_modify",
            MultiFileModifyExecutor(
                provider=self.modification,
            ),
        )
        self.registry.register(
            "project_analysis",
            ProjectAnalysisExecutor(
                provider=self.llm_provider,
            ),
        )
        self.registry.register(
            "fix_error",
            ErrorFixExecutor(),
        )
        self.registry.register(
            "summary",
            SummaryExecutor(),
        )

        for name, target in self.CONTRACTS.items():
            self.contract_registry.register(
                name,
                target,
            )

        resolver = ExecutorResolver(
            registry=self.registry,
            contract_registry=self.contract_registry,
        )

        if not resolver.ready():
            raise RuntimeError(
                "runtime executor assembly unavailable"
            )

        self.resolver = resolver
        return resolver

    def ready(self) -> bool:
        return (
            self.resolver is not None
            and self.resolver.ready()
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "contracts": tuple(
                self.CONTRACTS
            ),
            "resolver": (
                self.resolver.dump()
                if self.resolver is not None
                else None
            ),
            "ready": self.ready(),
        }

    @staticmethod
    def _validate(
        *,
        llm_provider: LLMExecutionProviderProtocol,
        tools: ToolExecutionPort,
        modification: CodeModificationProviderProtocol,
    ) -> None:
        values: dict[str, Any] = {
            "llm_provider": llm_provider,
            "tools": tools,
            "modification": modification,
        }

        for name, value in values.items():
            if value is None:
                raise ValueError(
                    f"{name} required"
                )

        if not isinstance(
            llm_provider,
            LLMExecutionProviderProtocol,
        ):
            raise TypeError(
                "llm provider runtime contract required"
            )

        if not isinstance(
            tools,
            ToolExecutionPort,
        ):
            raise TypeError(
                "tool execution port required"
            )

        if not isinstance(
            modification,
            CodeModificationProviderProtocol,
        ):
            raise TypeError(
                "code modification runtime contract required"
            )


__all__ = [
    "RuntimeExecutorAssembly",
]
