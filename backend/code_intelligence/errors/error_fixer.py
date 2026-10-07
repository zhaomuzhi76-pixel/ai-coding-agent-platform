from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any

from backend.code_intelligence.errors.error_parser import ErrorParser
from backend.code_intelligence.errors.error_signature import ErrorSignature
from backend.code_intelligence.errors.error_locator import ErrorLocator
from backend.code_intelligence.errors.error_verifier import ErrorVerifier
from backend.code_intelligence.memory.error_fix_store import ErrorFixStore


class ErrorFixer:
    """错误修复编排：解析 → 定位 → 查库/走orchestrator → 验证 → 学习。"""

    VERSION = "1.0"
    RESPONSIBILITY = ("error_fix_orchestration",)

    def __init__(self, orchestrator: Any | None = None,
                 gateway: Any | None = None,
                 router: Any | None = None) -> None:
        self.parser = ErrorParser()
        self.signature = ErrorSignature()
        self.locator = ErrorLocator()
        self.verifier = ErrorVerifier()
        self.store = ErrorFixStore.instance()
        self.orchestrator = orchestrator
        self.gateway = gateway
        self.router = router
        self.fix_count = 0
        self.cache_hit_count = 0

    async def fix(self, *, raw_error: str, workspace: str,
                  provider: str = "ollama") -> dict[str, Any]:
        self.fix_count += 1
        errors = self.parser.parse(raw_error)
        if not errors:
            return {"success": False, "error": "parse_failed"}
        error = errors[0]
        signature = self.signature.compute(error)

        loc = self.locator.locate(error, workspace=workspace)
        if not loc.get("success"):
            return {"success": False, "error": "locate_failed", "detail": loc}

        cached = self.store.lookup(signature)
        if cached and cached["success_count"] >= 2:
            print(f"[error-fixer] CACHE HIT sig={signature} "
                  f"count={cached['success_count']}", flush=True)
            self.cache_hit_count += 1
            return {"success": True, "source": "cache",
                    "signature": signature,
                    "patch": {"kind": cached["fix_kind"],
                              "text": cached["fix_text"]},
                    "target_file": loc["target_file"],
                    "error_type": error.error_type}

        if not self.orchestrator:
            return {"success": False, "error": "no_orchestrator",
                    "signature": signature}

        task = (f"修复 {loc['target_file']}:{loc['target_line']} 处的"
                f"{error.error_type}: {error.message}")

        # 收集调用链其他文件的内容
        related_files: dict[str, str] = {}
        primary = loc.get("target_file", "")
        for stack_file in loc.get("stack_files", []):
            if stack_file == primary:
                continue
            try:
                from pathlib import Path as _P
                full = _P(workspace) / stack_file
                if full.exists() and full.is_file():
                    txt = full.read_text(encoding="utf-8", errors="ignore")
                    related_files[stack_file] = txt
            except Exception as e:
                swallow("code_intelligence.errors.error_fixer:78", e)

        print(
            f"[error-fixer] related_files={list(related_files.keys())}",
            flush=True,
        )

        orch_result = await self.orchestrator.run(
            task=task,
            file=loc["target_file"],
            source=loc["full_source"],
            gateway=self.gateway,
            router=self.router,
            provider=provider,
            workspace=workspace,
            related_files=related_files,
        )

        if orch_result.get("success"):
            verify = self.verifier.verify(
                file=loc["target_file"], workspace=workspace,
            )
            if not verify.get("success"):
                self.store.record_failure(signature)
                return {"success": False, "error": "verify_failed",
                        "signature": signature, "verify": verify}
            self.store.record_success(
                signature=signature, error_type=error.error_type,
                error_message=error.message[:500],
                fix_kind=orch_result["patch"]["kind"],
                fix_text=orch_result["patch"]["text"],
                fix_plan=orch_result.get("plan", "")[:500],
                workspace=workspace,
            )
            print(f"[error-fixer] RECORDED sig={signature}", flush=True)
            return {"success": True, "source": "orchestrator",
                    "signature": signature,
                    "patch": orch_result["patch"],
                    "target_file": loc["target_file"],
                    "error_type": error.error_type}

        self.store.record_failure(signature)
        return {"success": False, "error": "orchestrator_failed",
                "signature": signature, "detail": orch_result}

    def ready(self) -> bool:
        return self.store.ready()

    def dump(self) -> dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "responsibility": self.RESPONSIBILITY,
                "ready": self.ready(),
                "fix_count": self.fix_count,
                "cache_hit_count": self.cache_hit_count}


__all__ = ["ErrorFixer"]
