from __future__ import annotations

import json
import re
from typing import Any

from backend.agent.orchestration.contracts import (
    EditContext,
    RoleResult,
)


class ReviewerAgent:
    """
    Reviewer: 用 7b 模型独立审查 coder 的 patch。

    Model: ROUTING_TABLE['review'] = qwen2.5-coder:7b
    """

    name = "reviewer"
    version = "1.0"

    SYSTEM_PROMPT = (
        "You are a strict code reviewer. "
        "Given a task and a proposed patch, decide if the patch "
        "correctly satisfies the task. "
        "The patch may use `kind:'replace_all'` (full file content in "
        "`text`) or `kind:'edit'` (list of {OLD, NEW} fragments in "
        "`edits`). For edit mode, verify that replacing OLD with NEW "
        "achieves the task. "
        "Reply with ONLY a JSON object with keys "
        "\"passed\" (true/false) and \"feedback\" (string). "
        "No markdown. No code fences."
    )

    async def run(
        self,
        *,
        context: EditContext,
        gateway: Any,
        router: Any,
        provider: str = "ollama",
    ) -> RoleResult:
        changes = context.extra.get("changes", []) or []
        user_prompt = self._build_user_prompt(context, changes)
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        try:
            result = await router.chat(
                gateway=gateway,
                task_type="review",
                provider=provider,
                messages=messages,
                format="json",
                temperature=0.0,
            )
            verdict = self._parse(str(result["response"]))
            print(
                f"[reviewer] passed={verdict['passed']} "
                f"feedback={verdict['feedback'][:80]!r} "
                f"model={result['model']}",
                flush=True,
            )
            return RoleResult(
                role=self.name,
                ok=True,
                data=verdict,
            )
        except Exception as error:
            return RoleResult(
                role=self.name,
                ok=False,
                data={},
                error=f"{type(error).__name__}: {error}",
            )

    @staticmethod
    def _parse(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            first = text.find("\n")
            last = text.rfind("```")
            if first >= 0 and last > first:
                text = text[first + 1:last].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                # 保守判定：无法解析就当通过
                return {"passed": True, "feedback": "unparsable review"}
            payload = json.loads(m.group(0))

        return {
            "passed": bool(payload.get("passed", True)),
            "feedback": str(payload.get("feedback", "")),
        }

    @staticmethod
    def _format_change(i: int, c: dict) -> str:
        """格式化单条 change（支持 replace_all / edit / prepend / append）。"""
        f = c.get("file", "?")
        k = c.get("kind", "?")
        if k == "edit":
            edits = c.get("edits") or []
            lines = [
                f"  [{i}] file={f!r} kind='edit' edits={len(edits)} 条:"
            ]
            for j, e in enumerate(edits[:5], 1):
                if not isinstance(e, dict):
                    continue
                old_frag = str(e.get("old", ""))[:200]
                new_frag = str(e.get("new", ""))[:200]
                lines.append(f"      edit#{j} OLD={old_frag!r}")
                lines.append(f"      edit#{j} NEW={new_frag!r}")
            return "\n".join(lines)
        t = str(c.get("text", ""))[:300]
        return (
            f"  [{i}] file={f!r} kind={k!r}\n"
            f"      text={t!r}"
        )

    @staticmethod
    def _build_user_prompt(
        context: EditContext,
        changes: list,
    ) -> str:
        head = "\n".join(context.source.split("\n")[:40])
        blocks: list[str] = [
            ReviewerAgent._format_change(i, c)
            for i, c in enumerate(changes[:5], 1)
        ]
        changes_str = "\n".join(blocks) if blocks else "  (no changes)"
        return (
            f"Task: {context.task}\n"
            f"Primary file: {context.file}\n\n"
            f"Plan: {context.plan}\n\n"
            "Source (first 40 lines of primary):\n"
            "----\n"
            f"{head}\n"
            "----\n\n"
            f"Proposed changes ({len(changes)} file(s)):\n"
            f"{changes_str}\n\n"
            "IMPORTANT: For `kind:'edit'`, each edit shows OLD (existing text) "
            "and NEW (replacement text). Verify that applying OLD→NEW would "
            "correctly achieve the task.\n\n"
            "Does this patch set correctly satisfy the task?\n"
            "Reply with JSON: {\"passed\": true|false, \"feedback\": \"...\"}"
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
        }


__all__ = ["ReviewerAgent"]
