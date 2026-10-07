"""Multi-file batch modification executor."""
from __future__ import annotations

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol
from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)

from backend.runtime.executors._shared.context_validator import (
    required_context_value,
)
from backend.runtime.executors._shared.metrics import ExecutorMetrics

from backend.runtime.executors.multi_file_modify_executor.change_builder import (
    build_changes,
)
from backend.runtime.executors.multi_file_modify_executor.contract import (
    NAME as _NAME,
    VERSION as _VERSION,
)
from backend.runtime.executors.multi_file_modify_executor.delta_extractor import (
    extract_delta,
)
from backend.runtime.executors.multi_file_modify_executor.file_loader import (
    load_files,
)
from backend.runtime.executors.multi_file_modify_executor.proposal_requester import (
    request_proposal,
)
from backend.runtime.executors.multi_file_modify_executor.validator import (
    resolve_root,
    validate_inputs,
)


class MultiFileModifyExecutor:
    """Batch multi-file modification with ONE LLM call."""

    VERSION = _VERSION
    name = _NAME

    def __init__(self, provider: CodeModificationProviderProtocol) -> None:
        if not isinstance(provider, CodeModificationProviderProtocol):
            raise TypeError("code modification provider contract required")
        self.provider = provider
        self._metrics = ExecutorMetrics()

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> dict:
        parameters = node.parameters
        files = parameters.get("files", [])
        instruction = parameters.get("instruction", "")
        task = parameters.get("message") or instruction or ""

        validate_inputs(files, task)
        root = resolve_root(context)
        provider = required_context_value("provider", context)
        model = required_context_value("model", context)

        self._metrics.mark_execution()
        try:
            loaded = load_files(root, files)
            if not loaded:
                raise RuntimeError("no non-empty files to modify")
            sample_path, sample_source = loaded[0]
            before, after = await request_proposal(
                self.provider, task, sample_path, sample_source,
                instruction, context, root, provider, model,
            )
            delta = extract_delta(before, after)
            changes = build_changes(loaded, delta, task)
            if not changes:
                raise RuntimeError("no effective changes")
            self._metrics.mark_success()
            return {
                "executor": _NAME,
                "status": "success",
                "changes": changes,
            }
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
            "execution_count": self._metrics.execution,
            "success_count": self._metrics.success,
            "failure_count": self._metrics.failure,
        }
