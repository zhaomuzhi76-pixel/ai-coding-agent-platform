"""Platform pipeline phases: apply / verify / learn.

拆出来保证 pipeline.py <= 230 行，单文件单职责。
所有阶段（含 noop 分支）都记录 span，便于观测。
"""
from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any, Callable, Dict, Optional

from backend.platform.proposal import Proposal
from backend.platform.session import CodingSession


class PipelinePhasesMixin:
    """Stage 4-7: apply / verify / learn.

    依赖宿主类提供：
        self._patch_executor, self._verifier, self._rollback
        self._events, self._memory, self.applied_count
    """

    def apply(
        self, session: CodingSession, proposal: Proposal,
        on_step: Optional[Callable[[dict], None]] = None,
    ) -> Dict[str, Any]:
        def _emit(ev: dict) -> None:
            if on_step is None:
                return
            try:
                on_step(ev)
            except Exception as e:
                swallow("platform.pipeline_phases:33", e, level="warn")

        _emit({"type": "stage", "name": "apply", "status": "start",
               "proposal_id": proposal.proposal_id,
               "file_count": proposal.file_count})

        if not self._gate.is_approved(proposal):
            _emit({"type": "error", "message": "proposal not approved"})
            raise RuntimeError("proposal not approved")

        with self._events.phase("pipeline.apply"):
            if self._patch_executor is None:
                proposal.transition("applied")
                session.add_turn(
                    "agent",
                    f"applied {proposal.proposal_id} (noop executor)",
                    proposal_id=proposal.proposal_id,
                )
                self.applied_count += 1
                return {"success": True, "applied": False,
                        "reason": "noop"}
            try:
                workspace = (
                    proposal.metadata.get("workspace", "") or "."
                )
                # 支持 BatchPatchExecutor 与单 PatchExecutor
                if hasattr(self._patch_executor, "execute_batch"):
                    # 1. LLM changes → patch dicts
                    from backend.platform.multi_file import (
                        changes_to_patches,
                    )
                    patches = changes_to_patches(
                        proposal.changes, workspace,
                    )
                    # 2. 原子批量执行（on_chunk 事件转发）
                    result = self._patch_executor.execute_batch(
                        patches, root=workspace,
                        on_chunk=lambda ev: _emit({
                            "type": "chunk", **ev,
                        }),
                    )
                    if not result.get("success"):
                        raise RuntimeError(
                            f"batch failed at "
                            f"{result.get('failed_at')}"
                        )
                else:
                    result = self._patch_executor.execute(
                        proposal.changes,
                    )
            except Exception as exc:
                proposal.transition("failed", str(exc))
                _emit({"type": "stage", "name": "apply", "status": "failed",
                       "proposal_id": proposal.proposal_id,
                       "error": str(exc)})
                raise

        proposal.transition("applied")
        self.applied_count += 1
        session.add_turn(
            "agent", f"applied {proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
        )
        _emit({"type": "stage", "name": "apply", "status": "done",
               "proposal_id": proposal.proposal_id})
        return result if isinstance(result, dict) else {"success": True}

    def verify(
        self, session: CodingSession, proposal: Proposal,
        workspace: str = "",
    ) -> Dict[str, Any]:
        with self._events.phase("pipeline.verify"):
            if self._verifier is None:
                session.add_turn(
                    "agent",
                    f"verified {proposal.proposal_id} (noop verifier)",
                    proposal_id=proposal.proposal_id,
                )
                return {"success": True, "verified": False,
                        "reason": "noop"}
            try:
                result = self._verifier.verify(
                    workspace or proposal.metadata.get("workspace", ""),
                )
            except Exception as exc:
                result = {"success": False, "error": str(exc)}

        ok = bool(result.get("success", False))
        if not ok and self._rollback is not None:
            with self._events.phase("pipeline.rollback"):
                try:
                    self._rollback.rollback()
                    proposal.transition("rolled_back")
                except Exception:
                    proposal.transition("failed")
            session.add_turn(
                "agent", f"rolled back {proposal.proposal_id}",
                proposal_id=proposal.proposal_id,
            )
        else:
            session.add_turn(
                "agent",
                f"verified {proposal.proposal_id}: "
                f"{'ok' if ok else 'fail'}",
                proposal_id=proposal.proposal_id,
            )
        return result if isinstance(result, dict) else {"success": ok}

    def learn(
        self, session: CodingSession, proposal: Proposal,
    ) -> None:
        with self._events.phase("pipeline.learn"):
            self._memory.on_accept(
                task=proposal.task, plan=proposal.plan,
                changes=proposal.changes,
                workspace=proposal.metadata.get("workspace", ""),
                model=proposal.metadata.get("model", ""),
                attempts=proposal.attempts,
            )


__all__ = ["PipelinePhasesMixin"]
