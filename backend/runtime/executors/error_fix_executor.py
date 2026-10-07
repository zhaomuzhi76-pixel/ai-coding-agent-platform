from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.core.context.kernel_context import KernelContext
from backend.core.execution import ExecutionNodeProtocol
from backend.application.planning.workspace_path_normalizer import (
    normalize_workspace_path,
)
from backend.runtime.executors.runtime_dependencies import (
    get_runtime_deps,
)


class ErrorFixExecutor:
    """fix_error runtime executor。"""

    VERSION = "1.1"
    name = "fix_error"

    def __init__(
        self,
        gateway: Any = None,
        router: Any = None,
        orchestrator: Any = None,
    ) -> None:
        self._gateway = gateway
        self._router = router
        self._orchestrator = orchestrator
        self.execution_count = 0
        self.success_count = 0

    def _resolve_deps(self) -> dict[str, Any]:
        """优先构造参数，回退全局注册表。"""
        if (self._gateway is not None and self._router is not None
                and self._orchestrator is not None):
            return {
                "gateway": self._gateway,
                "router": self._router,
                "orchestrator": self._orchestrator,
            }
        deps = get_runtime_deps()
        return {
            "gateway": self._gateway or deps.get("gateway"),
            "router": self._router or deps.get("router"),
            "orchestrator": self._orchestrator or deps.get("orchestrator"),
        }

    async def execute(
        self,
        node: ExecutionNodeProtocol,
        context: KernelContext,
    ) -> dict[str, object]:
        print("[error-fix-exec] ENTER execute()", flush=True)
        deps = self._resolve_deps()
        print(
            f"[error-fix-exec] deps "
            f"gateway={'OK' if deps['gateway'] else 'NONE'} "
            f"router={'OK' if deps['router'] else 'NONE'} "
            f"orchestrator={'OK' if deps['orchestrator'] else 'NONE'}",
            flush=True,
        )
        if not all(deps.values()):
            raise RuntimeError(
                "fix_error deps unavailable "
                f"(gateway={'OK' if deps['gateway'] else 'NONE'} "
                f"router={'OK' if deps['router'] else 'NONE'} "
                f"orchestrator={'OK' if deps['orchestrator'] else 'NONE'})"
            )

        params = node.parameters
        raw_error = (
            params.get("raw_error")
            or params.get("message")
            or params.get("instruction")
            or ""
        )
        if not isinstance(raw_error, str) or not raw_error.strip():
            raise ValueError("error_fix raw_error required")

        workspace = getattr(context, "workspace_id", None)
        if not isinstance(workspace, str) or not workspace.strip():
            workspace = context.get("workspace") or context.get("root")
        if not isinstance(workspace, str):
            raise RuntimeError("error_fix workspace required")
        workspace = normalize_workspace_path(workspace)

        provider = getattr(context, "provider", None) or "ollama"

        from backend.code_intelligence.errors import ErrorFixer
        fixer = ErrorFixer(
            orchestrator=deps["orchestrator"],
            gateway=deps["gateway"],
            router=deps["router"],
        )

        print(f"[error-fix-exec] fixing in {workspace}", flush=True)
        result = await fixer.fix(
            raw_error=raw_error,
            workspace=workspace,
            provider=provider,
        )

        self.execution_count += 1
        if not result.get("success"):
            raise RuntimeError(
                f"error_fix failed: {result.get('error')} "
                f"{result.get('detail', '')}"
            )
        self.success_count += 1

        # 支持多文件 changes
        patch_changes = result.get("changes") or []
        if not patch_changes:
            raise RuntimeError("error_fix: no changes in result")

        out_changes: list[dict[str, object]] = []
        for c in patch_changes:
            f = c.get("file")
            k = c.get("kind")
            t = c.get("text", "")
            if not f or not k:
                continue
            full = Path(workspace) / f
            try:
                before = full.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                before = ""
            after = self._apply_kind(before, k, t)
            out_changes.append({
                "file": f,
                "before": before,
                "after": after,
                "reason": result.get("error_type", "error fix"),
            })

        if not out_changes:
            raise RuntimeError("error_fix: no valid changes")

        print(
            f"[error-fix-exec] SUCCESS n_files={len(out_changes)} "
            f"source={result.get('source')} "
            f"sig={result.get('signature')} "
            f"files={[c['file'] for c in out_changes]}",
            flush=True,
        )

        return {
            "executor": self.name,
            "status": "success",
            "changes": out_changes,
        }

    @staticmethod
    def _apply_kind(source: str, kind: str, text: str) -> str:
        if kind == "prepend":
            return text + "\n" + source
        if kind == "append":
            if source and not source.endswith("\n"):
                return source + "\n" + text
            return source + text
        if kind == "replace_all":
            return text
        return source

    def ready(self) -> bool:
        # 装配期 deps 未注入；execute() 时再校验
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.VERSION,
            "ready": self.ready(),
            "execution_count": self.execution_count,
            "success_count": self.success_count,
        }


__all__ = ["ErrorFixExecutor"]
