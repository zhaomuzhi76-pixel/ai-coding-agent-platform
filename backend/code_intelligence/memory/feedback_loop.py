from __future__ import annotations
from backend.core.observability.silent import swallow

from typing import Any

from backend.code_intelligence.memory.memory_store import MemoryStore
from backend.code_intelligence.memory.session_log import SessionLog
from backend.code_intelligence.memory.skill_library import SkillLibrary
from backend.code_intelligence.memory.user_profile import UserProfileStore


class FeedbackLoop:
    """
    学习反馈统一入口。

    职责：
        - Accept：写 4 个 store（项目 patches + 会话 + 全局 skills + 偏好）
        - Reject：写 2 个 store（项目 patches + 偏好减弱）

    不职责：
        - 具体 SQLite 实现（各 store 自己管）
        - error_fixes（属于 ErrorFixer 专属）
    """

    VERSION = "2.0"

    def __init__(self) -> None:
        self.skills = SkillLibrary.instance()
        self.profile = UserProfileStore.instance()

    def on_accept(
        self,
        *,
        task: str,
        plan: str,
        kind: str,
        text: str,
        workspace: str,
    ) -> None:
        """用户/Reviewer 接受 → 强化所有 store。"""
        # 1. 项目级 patches
        if workspace:
            try:
                MemoryStore.for_workspace(workspace).record_patch(
                    task=task, plan=plan, kind=kind, text=text,
                    accepted=True, attempts=1,
                )
                print("[feedback] → memory_store.patches ✓", flush=True)
            except Exception as e:
                print(f"[feedback] memory_store fail: {e}", flush=True)

            # 2. 会话事件流
            try:
                SessionLog(workspace).append(
                    "patch_accepted",
                    {"task": task[:200], "kind": kind},
                )
                print("[feedback] → session_log ✓", flush=True)
            except Exception as e:
                print(f"[feedback] session_log fail: {e}", flush=True)

        # 3. 全局技能库
        try:
            self.skills.record(
                task=task, plan=plan, kind=kind,
                text=text, workspace=workspace or "",
            )
            print("[feedback] → skill_library ✓", flush=True)
        except Exception as e:
            print(f"[feedback] skill_library fail: {e}", flush=True)

        # 4. 用户偏好
        try:
            self.profile.observe(
                workspace=workspace or "",
                category="edit_style",
                signal="accepted_kind",
                payload={"key": "kind", "value": kind},
            )
            print("[feedback] → user_profile ✓", flush=True)
        except Exception as e:
            print(f"[feedback] user_profile fail: {e}", flush=True)

        print(
            f"[feedback] ACCEPT task={task[:40]!r} kind={kind!r}",
            flush=True,
        )

    def on_reject(
        self,
        *,
        task: str,
        kind: str,
        workspace: str,
    ) -> None:
        """用户拒绝 → 减弱偏好 + 记项目 patches。"""
        if workspace:
            try:
                MemoryStore.for_workspace(workspace).record_patch(
                    task=task, plan="", kind=kind, text="",
                    accepted=False, attempts=1,
                )
            except Exception as e:
                swallow("code_intelligence.memory.feedback_loop:104", e)

        try:
            self.profile.observe(
                workspace=workspace or "",
                category="edit_style",
                signal="rejected_kind",
                payload={"key": "kind", "value": kind},
            )
            self.profile.weaken("edit_style", "kind", delta=10)
        except Exception as e:
            swallow("code_intelligence.memory.feedback_loop:115", e)

        print(
            f"[feedback] REJECT task={task[:40]!r} kind={kind!r}",
            flush=True,
        )

    def render_user_context(self) -> str:
        return self.profile.render_context(limit=8)

    def ready(self) -> bool:
        return self.skills is not None and self.profile is not None

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = ["FeedbackLoop"]
