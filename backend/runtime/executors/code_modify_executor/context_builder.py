"""构造 provider.execute 所需的上下文字典。"""
from __future__ import annotations

from typing import Any, Dict

from backend.core.context.kernel_context import KernelContext

from backend.runtime.executors._shared.context_validator import (
    required_context_value,
)
from backend.runtime.executors.code_modify_executor.contract import (
    RequestData,
)


def build_provider_context(
    context: KernelContext, req: RequestData,
) -> Dict[str, Any]:
    return {
        "runtime_context": context,
        "files": list(req.files),
        "source": req.source,
        "instruction": req.instruction,
        "changes": dict(req.changes or {}),
        "provider": required_context_value("provider", context),
        "model": required_context_value("model", context),
        "root": req.workspace_root,
    }
