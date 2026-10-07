from __future__ import annotations

from typing import Any

from backend.agent.orchestration.contracts import (
    EditContext,
    RoleResult,
)


class PlannerAgent:
    """
    Planner: 用强模型输出改动策略（纯文本，不含代码）。

    Model: ROUTING_TABLE['plan'] = qwen2.5-coder:7b
    """

    name = "planner"
    version = "1.0"

    SYSTEM_PROMPT = (
        "You are a senior software engineer. "
        "Given a task and source code, produce a SHORT plan. "
        "The plan must state WHAT to change in 1-3 sentences. "
        "Do NOT output code. Do NOT output JSON. Only plain text."
    )

    async def run(
        self,
        *,
        context: EditContext,
        gateway: Any,
        router: Any,
        provider: str = "ollama",
    ) -> RoleResult:
        user_prompt = self._build_user_prompt(context)
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        try:
            result = await router.chat(
                gateway=gateway,
                task_type="plan",
                provider=provider,
                messages=messages,
                temperature=0.0,
            )
            plan = str(result["response"]).strip()
            print(
                f"[planner] plan={plan[:120]!r} "
                f"model={result['model']}",
                flush=True,
            )
            return RoleResult(
                role=self.name,
                ok=True,
                data={"plan": plan},
            )
        except Exception as error:
            return RoleResult(
                role=self.name,
                ok=False,
                data={},
                error=f"{type(error).__name__}: {error}",
            )

    @staticmethod
    def _build_user_prompt(context: EditContext) -> str:
        head = "\n".join(context.source.split("\n")[:60])
        return (
            f"Task: {context.task}\n"
            f"File: {context.file}\n\n"
            "Source (first 60 lines):\n"
            "----\n"
            f"{head}\n"
            "----\n\n"
            "Produce a short plan (1-3 sentences)."
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "ready": self.ready(),
        }


__all__ = ["PlannerAgent"]
