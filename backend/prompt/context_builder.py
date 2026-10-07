from __future__ import annotations

from typing import Any

from backend.core.context.runtime_context import RuntimeContext


class PromptContextBuilder:
    """
    Build prompt sections from RuntimeContext.

    Responsibility:
        - convert context into prompt sections

    Not Responsible:
        - prompt template loading
        - LLM calling
        - memory storage
    """

    VERSION = "3.3"

    def build(
        self,
        context: RuntimeContext,
    ) -> dict[str, str]:
        if context is None:
            raise ValueError(
                "runtime context required"
            )

        sections: dict[str, str] = {}

        sections["system"] = (
            "You are an AI coding assistant."
        )

        sections["memory"] = (
            self._build_memory(context)
        )

        sections["workspace"] = (
            self._build_workspace(context)
        )

        sections["planner"] = (
            self._build_planner(context)
        )

        sections["runtime"] = (
            self._build_runtime(context)
        )

        sections["task"] = (
            self._build_task(context)
        )

        reflection = (
            self._build_reflection(context)
        )

        if reflection:
            sections["reflection"] = reflection

        return sections

    def _build_memory(
        self,
        context: RuntimeContext,
    ) -> str:
        memory = getattr(
            context,
            "memory",
            {},
        )

        if hasattr(memory, "dump"):
            memory = memory.dump()

        return (
            f"Memory Context:\n{memory}"
        )

    def _build_workspace(
        self,
        context: RuntimeContext,
    ) -> str:
        return (
            "Workspace Context:\n"
            f"{getattr(context, 'workspace', {})}"
        )

    def _build_planner(
        self,
        context: RuntimeContext,
    ) -> str:
        return (
            "Planner:\n"
            f"{getattr(context, 'planner', {})}"
        )

    def _build_runtime(
        self,
        context: RuntimeContext,
    ) -> str:
        runtime = getattr(
            context,
            "runtime_context",
            None,
        )

        if runtime is not None:
            if hasattr(runtime, "dump"):
                runtime = runtime.dump()
            else:
                runtime = str(runtime)
        else:
            runtime = getattr(
                context,
                "runtime",
                {},
            )

        return (
            f"Runtime:\n{runtime}"
        )

    def _build_task(
        self,
        context: RuntimeContext,
    ) -> str:
        execution = getattr(
            context,
            "execution",
            {},
        )

        if hasattr(execution, "dump"):
            execution = execution.dump()

        return (
            f"Task:\n{execution}"
        )

    def _build_reflection(
        self,
        context: RuntimeContext,
    ) -> str | None:
        reflection = getattr(
            context,
            "reflection_context",
            None,
        )

        if reflection is None:
            return None

        if hasattr(reflection, "dump"):
            reflection = reflection.dump()

        return (
            "Reflection:\n"
            f"{reflection}"
        )

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "capabilities": [
                "context_building",
                "memory_context",
                "workspace_context",
                "planner_context",
                "runtime_context",
                "task_context",
                "reflection_context",
            ],
        }


__all__ = [
    "PromptContextBuilder",
]
