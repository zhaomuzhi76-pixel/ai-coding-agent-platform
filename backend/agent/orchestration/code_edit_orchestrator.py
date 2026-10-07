"""L4-B 编辑流水线（三角色 → 确定性预检 → 编译验证）。

Responsibility:
    - Planner → Coder → Precheck → LocalVerify 固定流程
    - 不做 LLM reviewer（避免幻觉）
    - 最多 MAX_ATTEMPTS 轮
    - 通过后落盘三层记忆

Not Responsible:
    - 交互式循环（L4-A）
    - 后台任务编排（L4-C）

调用方：backend/platform/pipeline.py（L3）
"""
from __future__ import annotations

from typing import Any

from backend.agent.orchestration.contracts import (
    EditContext, RoleResult,
)
from backend.agent.orchestration.planner_agent import PlannerAgent
from backend.agent.orchestration.coder_agent import CoderAgent
from backend.agent.orchestration.reviewer_agent import ReviewerAgent
from backend.agent.orchestration.code_edit_persistence import (
    CodeEditPersistence,
)
from backend.agent.orchestration.local_verifier import LocalVerifier
from backend.agent.orchestration.rules_verifier import (
    RulesVerifier,
)
from backend.agent.orchestration.edit_precheck import EditPrecheck
from backend.agent.orchestration.orchestrator_support import (
    as_trace, emit_file_changes, make_fail_result, verify_locally,
)


class CodeEditOrchestrator:
    """Manager loop for multi-file code edit."""

    VERSION = "4.0"
    MAX_ATTEMPTS = 3

    def __init__(
        self,
        *,
        planner: PlannerAgent | None = None,
        coder: CoderAgent | None = None,
        reviewer: ReviewerAgent | None = None,
        persistence: CodeEditPersistence | None = None,
        max_attempts: int | None = None,
    ) -> None:
        self.planner = planner or PlannerAgent()
        self.coder = coder or CoderAgent()
        self.reviewer = reviewer or ReviewerAgent()
        self.persistence = persistence or CodeEditPersistence()
        self.max_attempts = max_attempts or self.MAX_ATTEMPTS
        self._local_verifier = LocalVerifier()
        self._edit_precheck = EditPrecheck()
        self._rules_verifier_factory = RulesVerifier
        self.run_count = 0
        self.success_count = 0

    async def run(
        self,
        *,
        task: str,
        file: str,
        source: str,
        gateway: Any,
        router: Any,
        provider: str = "ollama",
        workspace: str = "",
        related_files: dict[str, str] | None = None,
        stream_callback: Any = None,
    ) -> dict[str, Any]:
        self.run_count += 1
        trace: list[dict[str, Any]] = []

        extra: dict[str, Any] = {}
        if workspace:
            extra["workspace"] = workspace
        if related_files:
            extra["related_files"] = related_files

        context = EditContext(
            task=task, file=file, source=source,
            max_attempts=self.max_attempts,
            related_files=related_files or {},
            extra=extra,
        )

        # ── Step 1: Plan ──
        plan_result: RoleResult = await self.planner.run(
            context=context, gateway=gateway,
            router=router, provider=provider,
        )
        trace.append(as_trace(plan_result))
        if plan_result.ok:
            context.plan = str(plan_result.data.get("plan", ""))
        else:
            return make_fail_result(
                "planner", trace, plan_result.error)

        # ── Step 2-4: Coder → Precheck → Verify loop ──
        for attempt in range(1, self.max_attempts + 1):
            context.attempt = attempt
            print(f"[orchestrator] attempt {attempt}/{self.max_attempts}",
                  flush=True)

            coder_result: RoleResult = await self.coder.run(
                context=context, gateway=gateway,
                router=router, provider=provider,
                stream_callback=stream_callback,
            )
            trace.append(as_trace(coder_result))
            if not coder_result.ok:
                context.prior_feedback = (
                    f"coder failed: {coder_result.error}"
                )
                continue

            changes = coder_result.data.get("changes", [])
            context.extra["changes"] = changes

            # 向前端推 file_change
            await emit_file_changes(stream_callback, changes)

            # 确定性预检（避免 LLM reviewer 幻觉）
            precheck = self._edit_precheck.check(
                workspace=workspace, changes=changes,
            )
            if not precheck.ok:
                issues_txt = "\n".join(
                    f"  - {i.to_line()}"
                    for i in precheck.issues[:5]
                )
                context.prior_feedback = (
                    f"[Deterministic precheck FAILED]\n"
                    f"{issues_txt}\n"
                    "Please fix the above issues and retry."
                )
                print(
                    f"[orchestrator] precheck FAILED at attempt "
                    f"{attempt}: {len(precheck.issues)} issues",
                    flush=True,
                )
                continue

            print(
                f"[orchestrator] precheck PASS "
                f"({len(precheck.applied_files)} files)",
                flush=True,
            )

            # 工业级：跳过 LLM reviewer（幻觉源），直接本地验证
            trace.append({
                "role": "reviewer", "ok": True,
                "data": {"passed": True, "skipped": True,
                         "reason": "precheck passed"},
                "error": None,
            })

            verify_ok = await verify_locally(
                workspace=workspace, changes=changes,
                context=context, verifier=self._local_verifier,
            )
            if not verify_ok:
                print(
                    f"[orchestrator] local verify FAILED at "
                    f"attempt {attempt}, retrying",
                    flush=True,
                )
                continue

            # ── 工业级：用户规则硬校验（生成后真跑 checker） ──
            rv = self._rules_verifier_factory(workspace=workspace)
            fb = rv.verify_changes(changes)
            if not fb.ok:
                context.prior_feedback = fb.to_prompt()
                print(
                    f"[orchestrator] rules verify FAILED at "
                    f"attempt {attempt}: {len(fb.violations)} violations",
                    flush=True,
                )
                continue
            print(
                f"[orchestrator] rules verify PASS "
                f"({fb.checked_rules} rules)",
                flush=True,
            )

            self.success_count += 1
            print(f"[orchestrator] success at attempt {attempt}",
                  flush=True)
            self.persistence.persist_accept(
                task=task, plan=context.plan,
                changes=changes, workspace=workspace,
                attempt=attempt,
            )
            return {
                "success": True,
                "changes": changes,
                "plan": context.plan,
                "attempts": attempt,
                "trace": trace,
            }

        return make_fail_result(
            "max_attempts_exhausted", trace,
            context.prior_feedback or "review never passed",
        )


__all__ = ["CodeEditOrchestrator"]
