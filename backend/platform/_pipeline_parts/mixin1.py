"""Mixin 1 of PlatformPipeline."""
from __future__ import annotations
from .part1 import (Any, ApprovalGate, CodingRequest, CodingSession, Dict, EventBridge, MemoryBridge, Optional, Proposal, normalize_workspace_path,)  # noqa: F401
class _Mixin1:
    def __init__(
        self,
        *,
        orchestrator: Any,
        approval_gate: Optional[ApprovalGate] = None,
        event_bridge: Optional[EventBridge] = None,
        memory_bridge: Optional[MemoryBridge] = None,
        patch_executor: Optional[Any] = None,
        verification_runner: Optional[Any] = None,
        patch_rollback: Optional[Any] = None,
    ) -> None:
        if orchestrator is None:
            raise ValueError("orchestrator required")
        self._orchestrator = orchestrator
        self._gate = approval_gate or ApprovalGate()
        self._events = event_bridge or EventBridge()
        self._memory = memory_bridge or MemoryBridge()
        self._patch_executor = patch_executor
        self._verifier = verification_runner
        self._rollback = patch_rollback
        self.proposal_count = 0
        self.applied_count = 0
        self._proposals: Dict[str, Proposal] = {}

    async def propose(
        self,
        session: CodingSession,
        request: CodingRequest,
        *,
        gateway: Any = None,
        router: Any = None,
        provider: str = "",
        event_callback: Any = None,
        user_routing: Any = None,
    ) -> Proposal:
        request.validate()

        # ── 工业级：用户消息 → 自动学习规则（持久化）──
        try:
            from backend.agent_learning.auto_learner import get_default
            learned = get_default().learn_from_message(
                request.task,
                workspace=getattr(request, "workspace", "") or "",
            )
            if learned:
                print(
                    f"[auto-learn] {len(learned)} 条规则: "
                    f"{[r['key'] for r in learned]}",
                    flush=True,
                )
        except Exception as e:
            print(f"[auto-learn] error: {e}", flush=True)

        session.touch()
        session.add_turn(
            "user", request.task,
            files=request.files, model=request.model,
        )

        primary_file = normalize_workspace_path(request.normalized_files()[0])
        # 工业级：区分"改已有文件" vs "新建文件"两种场景
        from backend.workspace.file_ops import exists as _file_exists
        workspace_norm = normalize_workspace_path(request.workspace)
        is_new_file = not _file_exists(workspace_norm, primary_file)
        try:
            source = self._read_primary(
                workspace_norm, primary_file,
                allow_missing=is_new_file,
            )
        except OSError as exc:
            raise RuntimeError(
                f"cannot read primary file {primary_file}: {exc}"
            ) from exc

        # 新文件场景：通知下游和前端（前端可显示"新建"图标）
        if is_new_file:
            print(
                f"[pipeline.propose] new file mode: {primary_file}",
                flush=True,
            )
            await self._emit(event_callback, {
                "event": "new_file",
                "file": primary_file,
                "workspace": workspace_norm,
            })

        # 自动从 primary_file 的 import 解析相关文件
        related: dict = {}
        try:
            from backend.platform.multi_file.context_resolver import (
                resolve_related_files,
            )
            related = resolve_related_files(
                request.workspace, primary_file,
            )
            if related:
                await self._emit(event_callback, {
                    "event": "related_files",
                    "files": list(related.keys()),
                })
                print(
                    f"[pipeline.propose] auto-related="
                    f"{list(related.keys())}",
                    flush=True,
                )
        except Exception as exc:
            print(
                f"[pipeline.propose] resolve related failed: {exc}",
                flush=True,
            )

        await self._emit(event_callback, {
            "event": "stage", "name": "propose", "status": "running",
        })

        async def _stream_cb(evt: dict) -> None:
            await self._emit(event_callback, evt)

        # user_routing 覆盖：构造新的 ModelRouter
        if user_routing is not None:
            try:
                from backend.application.provider_gateway.model_router import (
                    ModelRouter,
                )
                router = ModelRouter(user_routing=user_routing)
            except Exception as exc:
                print(
                    f"[pipeline.propose] user_routing failed: {exc}",
                    flush=True,
                )

        print(
            f"[pipeline-propose-debug] provider={provider!r} "
            f"request.model={request.model!r} "
            f"orchestrator_provider={provider or request.model!r}",
            flush=True,
        )
        with self._events.phase("pipeline.propose"):
            result = await self._orchestrator.run(
                task=request.task,
                file=primary_file,
                source=source,
                gateway=gateway,
                router=router,
                provider=provider or request.model,
                workspace=request.workspace,
                related_files=related or None,
                stream_callback=_stream_cb,
            )

        self.proposal_count += 1
        if not result.get("success"):
            session.add_turn(
                "agent", f"proposal failed: {result.get('error')}",
                reason=result.get("reason"),
            )
            raise RuntimeError(
                f"proposal failed: {result.get('reason')} "
                f"{result.get('error')}"
            )

        proposal = Proposal(
            task=request.task,
            plan=str(result.get("plan", "")),
            changes=list(result.get("changes", [])),
            attempts=int(result.get("attempts", 1)),
            trace=list(result.get("trace", [])),
            metadata={
                "model": request.model,
                "locale": request.locale,
                "workspace": request.workspace,
                "session_id": session.session_id,
            },
        )
        self._gate.request_for_proposal(proposal)
        self._proposals[proposal.proposal_id] = proposal
        await self._emit(event_callback, {
            "event": "done",
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "plan": proposal.plan,
            "changes": proposal.changes,
        })
        session.add_turn(
            "agent",
            f"proposal {proposal.proposal_id} generated "
            f"({proposal.file_count} files)",
            proposal_id=proposal.proposal_id,
        )
        return proposal

    def approve(
        self, session: CodingSession, proposal: Proposal,
    ) -> None:
        self._gate.approve(proposal)
        session.add_turn(
            "user", f"approved {proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
        )
