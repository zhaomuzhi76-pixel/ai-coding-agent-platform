"""处理 provider.execute 返回结果。"""
from __future__ import annotations

from typing import Any, Dict

from backend.runtime.executors.code_modify_executor.contract import (
    NAME,
    ProviderResult,
)


def handle_provider_result(result: Any) -> ProviderResult:
    if not isinstance(result, dict):
        raise TypeError("modification result must dict")
    success = bool(result.get("success", False))
    if not success:
        detail = (
            result.get("error")
            or result.get("message")
            or "code modification failed"
        )
        raise RuntimeError(str(detail))
    return {
        "executor": NAME,
        "status": "success",
        "result": result,
    }
