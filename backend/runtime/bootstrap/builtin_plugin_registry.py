from __future__ import annotations

from backend.core.code_intelligence.analysis_port import (
    CodeAnalyzerProtocol,
)
from backend.core.code_intelligence.workspace_port import (
    CodeIntelligenceWorkspaceProtocol,
)
from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)
from backend.runtime.plugins.code_modification import (
    CodeModificationRuntimePlugin,
)
from backend.runtime.bootstrap.tool_runtime_provider import (
    RuntimeToolRuntimeProvider,
)
from backend.runtime.plugins.code_intelligence.plugin import (
    CodeIntelligenceRuntimePlugin,
)
from backend.runtime.plugins.tools.plugin import (
    ToolRuntimePlugin,
)
from backend.runtime.plugins.dag_engine.plugin import (
    DAGExecutionPlugin,
)
from backend.runtime.plugins.executors.plugin import (
    RuntimeExecutorPlugin,
)
from backend.runtime.plugins.knowledge.plugin import (
    KnowledgeRuntimePlugin,
)
from backend.runtime.plugins.node_events.plugin import (
    NodeEventPlugin,
)
from backend.runtime.plugins.intelligence.plugin import (
    IntelligenceRuntimePlugin,
)


def builtin_plugins(
    *,
    tool_runtime_provider: RuntimeToolRuntimeProvider,
    workspace_root: str,
    code_intelligence_workspace: CodeIntelligenceWorkspaceProtocol,
    code_intelligence_resolver=None,
    code_modification_provider: CodeModificationProviderProtocol,
    code_analyzer: CodeAnalyzerProtocol,
) -> tuple[tuple[str, object], ...]:
    if not isinstance(
        tool_runtime_provider,
        RuntimeToolRuntimeProvider,
    ):
        raise TypeError(
            "tool runtime provider must "
            "RuntimeToolRuntimeProvider"
        )

    if not isinstance(
        workspace_root,
        str,
    ) or not workspace_root.strip():
        raise ValueError(
            "workspace root required"
        )

    if not isinstance(
        code_intelligence_workspace,
        CodeIntelligenceWorkspaceProtocol,
    ):
        raise TypeError(
            "code intelligence workspace contract required"
        )

    if not isinstance(
        code_modification_provider,
        CodeModificationProviderProtocol,
    ):
        raise TypeError(
            "code modification provider contract required"
        )

    if not isinstance(
        code_analyzer,
        CodeAnalyzerProtocol,
    ):
        raise TypeError(
            "code analyzer contract required"
        )

    return (
        (
            "events",
            NodeEventPlugin(),
        ),
        (
            "execution",
            DAGExecutionPlugin(),
        ),
        (
            "executor",
            RuntimeExecutorPlugin(),
        ),
        (
            "knowledge",
            KnowledgeRuntimePlugin(),
        ),
        (
            "intelligence",
            IntelligenceRuntimePlugin(),
        ),
        (
            "code_intelligence",
            CodeIntelligenceRuntimePlugin(
                workspace=code_intelligence_workspace,
                resolver=code_intelligence_resolver,
            ),
        ),
        (
            "code_modification",
            CodeModificationRuntimePlugin(
                provider=code_modification_provider,
            ),
        ),
        (
            "tools",
            ToolRuntimePlugin(
                tool_runtime_provider
            ),
        ),
    )


__all__ = [
    "builtin_plugins",
]
