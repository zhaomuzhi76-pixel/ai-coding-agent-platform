"""CodeModifyExecutor 门面类：编排提取、校验、调用与结果处理。"""
from __future__ import annotations

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol
from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)
from backend.application.planning.workspace_path_normalizer import (
    normalize_workspace_path,
)

from backend.runtime.executors.code_modify_executor.contract import (
    NAME as _NAME,
    VERSION as _VERSION,
)
from backend.runtime.executors.code_modify_executor.context_builder import (
    build_provider_context,
)
from backend.runtime.executors.code_modify_executor.metrics import (
    ExecutorMetrics,
)
from backend.runtime.executors.code_modify_executor.path_resolver import (
    resolve_path,
)
from backend.runtime.executors.code_modify_executor.request_extractor import (
    extract_request,
)
from backend.runtime.executors.code_modify_executor.request_validator import (
    validate_request,
)
from backend.runtime.executors.code_modify_executor.result_handler import (
    handle_provider_result,
)
from backend.runtime.executors.code_modify_executor.source_loader import (
    ensure_source,
)


class CodeModifyExecutor:
    """Runtime code modification execution adapter."""

    VERSION = _VERSION
    name = _NAME

    def __init__(
        self,
        provider: CodeModificationProviderProtocol,
    ) -> None:
        if not isinstance(provider, CodeModificationProviderProtocol):
            raise TypeError(
                "code modification provider contract required"
            )
        self.provider = provider
        self._metrics = ExecutorMetrics()

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> dict:
        self._validate_node(node)
        workspace_root = normalize_workspace_path(
            str(context.workspace_id)
        )
        req = extract_request(node, context, workspace_root)

        # LLM 只给文件名时，在工作区搜索唯一命中（Codex/Claude Code 同款）
        if req.path:
            req.path = resolve_path(workspace_root, req.path)
            if req.path and req.files:
                req.files = [req.path] + list(req.files[1:])

        req.source = ensure_source(req.source, workspace_root, req.path)
        validate_request(req)
        self._metrics.mark_execution()
        try:
            result = await self.provider.execute(
                task=req.task,
                files=req.files,
                context=build_provider_context(context, req),
            )
            payload = handle_provider_result(result)
            self._metrics.mark_success()
            return payload
        except Exception:
            self._metrics.mark_failure()
            raise

    def ready(self) -> bool:
        return self.provider.ready()

    def dump(self) -> dict:
        return {
            "name": self.name,
            "version": self.VERSION,
            "ready": self.ready(),
            "metrics": self._metrics.as_dict(),
        }

    @staticmethod
    def _validate_node(node: ExecutionNodeProtocol) -> None:
        if not isinstance(node, ExecutionNodeProtocol):
            raise TypeError("node must ExecutionNodeProtocol")
