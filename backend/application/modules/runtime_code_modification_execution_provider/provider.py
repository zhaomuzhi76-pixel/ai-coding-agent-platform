"""Application owner of modification proposal/execution composition."""
from __future__ import annotations

from typing import Any

from backend.application.capability.code_modification_proposal_adapter import (
    CodeModificationProposalAdapter,
)
from backend.core.execution.code_modification_contract import (
    CodeModificationProviderProtocol,
)

from backend.runtime.executors._shared.context_validator import (
    required_context_value,
)
from backend.runtime.executors._shared.kind_applier import apply_kind
from backend.runtime.executors._shared.metrics import ExecutorMetrics

from backend.application.modules.runtime_code_modification_execution_provider.contract import (
    VERSION as _VERSION,
)
from backend.application.modules.runtime_code_modification_execution_provider.multi_agent_runner import (
    run_multi_agent,
)
from backend.application.modules.runtime_code_modification_execution_provider.result_builder import (
    build_result,
)
from backend.application.modules.runtime_code_modification_execution_provider.single_agent_runner import (
    run_single_agent,
)
from backend.application.modules.runtime_code_modification_execution_provider.validator import (
    validate_request,
)


class RuntimeCodeModificationExecutionProvider(
    CodeModificationProviderProtocol,
):
    """Application owner of modification proposal/execution composition."""

    VERSION = _VERSION

    def __init__(
        self,
        *,
        proposal: CodeModificationProposalAdapter,
        pipeline: Any,
        gateway: Any | None = None,
        router: Any | None = None,
        orchestrator: Any | None = None,
    ) -> None:
        if not isinstance(proposal, CodeModificationProposalAdapter):
            raise TypeError("proposal adapter required")
        if pipeline is None:
            raise ValueError("modification pipeline required")
        ready = getattr(pipeline, "ready", None)
        if not callable(ready) or not ready():
            raise RuntimeError("modification pipeline unavailable")
        self.proposal = proposal
        self.pipeline = pipeline
        self.gateway = gateway
        self.router = router
        self.orchestrator = orchestrator
        self._metrics = ExecutorMetrics()
        self.multi_agent_count = 0

    async def execute(
        self,
        *,
        task: str,
        files: list,
        context: dict,
    ) -> object:
        file = validate_request(task, files, context)
        runtime_context = context.get("runtime_context")
        provider = required_context_value(
            "provider", context, runtime_context,
        )
        model = required_context_value(
            "model", context, runtime_context,
        )
        self._metrics.mark_execution()
        try:
            use_multi = (
                self.orchestrator is not None
                and self.gateway is not None
                and self.router is not None
            )
            if use_multi:
                self.multi_agent_count += 1
                kind, text, _ = await run_multi_agent(
                    self.orchestrator, self.gateway, self.router,
                    provider, task, file, context["source"],
                )
            else:
                kind, text = await run_single_agent(
                    self.proposal, task, file, context["source"],
                    provider, model, context,
                )
            result = build_result(
                file, kind, text, context["source"], task, apply_kind,
            )
            self._metrics.mark_success()
            return result
        except Exception:
            self._metrics.mark_failure()
            raise

    def ready(self) -> bool:
        pipeline_ready = getattr(self.pipeline, "ready", lambda: False)
        return self.proposal.ready() and bool(pipeline_ready())

    def dump(self) -> dict:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            **self._metrics.as_dict(),
            "multi_agent_count": self.multi_agent_count,
            "multi_agent_enabled": self.orchestrator is not None,
            "proposal": type(self.proposal).__name__,
            "pipeline": type(self.pipeline).__name__,
        }


__all__ = ["RuntimeCodeModificationExecutionProvider"]
