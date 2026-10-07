from __future__ import annotations

from typing import Any


class CodeEditPersistence:
    """
    编辑任务成功后的统一落盘。

    支持单 patch 或 changes 列表。三层记忆：
        1. 项目记忆 (MemoryStore.patches)
        2. 会话记忆 (SessionLog JSONL)
        3. 全局记忆 (SkillLibrary + UserProfileStore)
    """

    VERSION = "1.1"
    RESPONSIBILITY = ("code_edit_persistence",)

    def persist_accept(
        self,
        *,
        task: str,
        plan: str,
        changes: list[dict[str, Any]],
        workspace: str,
        attempt: int = 1,
    ) -> None:
        if not changes:
            return

        summary_kind = changes[0].get("kind", "")
        summary_text = "\n".join(
            f"=== {c.get('file', '?')} ===\n{c.get('text', '')}"
            for c in changes
        )

        if workspace:
            try:
                from backend.code_intelligence.memory import MemoryStore
                MemoryStore.for_workspace(workspace).record_patch(
                    task=task, plan=plan,
                    kind=str(summary_kind), text=summary_text,
                    accepted=True, attempts=attempt,
                )
                print("[persist] → 项目记忆 memory_store.patches ✓",
                      flush=True)
            except Exception as e:
                print(f"[persist] 项目记忆失败: {type(e).__name__}: {e}",
                      flush=True)

            try:
                from backend.code_intelligence.memory import SessionLog
                SessionLog(workspace).append(
                    "patch_accepted",
                    {"task": task[:200],
                     "n_files": len(changes),
                     "files": [c.get("file") for c in changes]},
                )
                print("[persist] → 会话记忆 session.jsonl ✓",
                      flush=True)
            except Exception as e:
                print(f"[persist] 会话记忆失败: {type(e).__name__}: {e}",
                      flush=True)

        try:
            from backend.code_intelligence.memory import FeedbackLoop
            FeedbackLoop().on_accept(
                task=task, plan=plan,
                kind=str(summary_kind), text=summary_text,
                workspace=workspace or "",
            )
            print("[persist] → 全局记忆 skill+preference ✓",
                  flush=True)
        except Exception as e:
            print(f"[persist] 全局记忆失败: {type(e).__name__}: {e}",
                  flush=True)

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {"name": type(self).__name__, "version": self.VERSION,
                "responsibility": self.RESPONSIBILITY,
                "ready": self.ready()}


__all__ = ["CodeEditPersistence"]
