from __future__ import annotations

from typing import Any

from backend.agent.planner.models.planner_intent import (
    PlannerIntent,
)


class IntentResolver:
    """
    Resolve TaskAnalysis into planner intent.

    Responsibility:

        - create planner intent contract
        - apply deterministic intent fallback rules

    Not Responsible:

        - task classification
        - route selection
        - step creation
        - execution
    """

    VERSION = "4.0"

    RESPONSIBILITY = (
        "planner_intent_resolution",
    )

    VALID_INTENTS = {
        "workspace_scan",
        "code_analysis",
        "file_edit",
        "file_read",
        "file_write",
        "test",
        "deployment",
        "summary",
        "text_generate",
        "understand_project",
        "edit_multiple_files",
        "create_project",
    }

    WORKSPACE_KEYWORDS = (
        "系统架构",
        "项目结构",
        "代码结构",
        "分析我的系统",
        "分析项目",
        "扫描项目",
        "workspace",
        "project",
        "architecture",
    )

    def resolve(
        self,
        analysis: Any,
    ) -> PlannerIntent:

        intent_name = self._resolve_name(
            analysis
        )

        return PlannerIntent(
            name=intent_name,

            parameters=dict(
                getattr(
                    analysis,
                    "parameters",
                    {},
                )
            ),

            capabilities=list(
                getattr(
                    analysis,
                    "required_capabilities",
                    [],
                )
            ),

            complexity=getattr(
                analysis,
                "complexity",
                "simple",
            ),

            risk_level=getattr(
                analysis,
                "risk_level",
                "low",
            ),
        )

    # 强烈表示"理解项目"的特征词
    UNDERSTAND_HINTS = (
        "做什么", "干什么", "介绍", "优势", "短板", "优缺点",
        "设计理念", "任务是", "目标是", "用来", "的作用",
        "设计思路", "整体介绍", "简述",
        "what does", "what is", "introduce", "purpose",
        "advantages", "disadvantages", "overview",
    )

    def _resolve_name(
        self,
        analysis: Any,
    ) -> str:

        # ★ 前置：understand_project 特征词优先于关键词规则
        message = str(
            getattr(analysis, "message", "")
        ).lower()
        if any(h in message for h in self.UNDERSTAND_HINTS):
            return "understand_project"

        task_type = getattr(
            analysis,
            "task_type",
            None,
        )

        if task_type in self.VALID_INTENTS:
            return task_type

        message = str(
            getattr(
                analysis,
                "message",
                "",
            )
        ).lower()

        if self._is_workspace_request(
            message
        ):
            return "workspace_scan"

        capabilities = getattr(
            analysis,
            "required_capabilities",
            (),
        )

        if "file_edit" in capabilities:
            return "file_edit"

        return "text_generate"

    def _is_workspace_request(
        self,
        message: str,
    ) -> bool:

        return any(
            keyword.lower()
            in message
            for keyword in self.WORKSPACE_KEYWORDS
        )

    def ready(
        self,
    ) -> bool:

        return bool(
            self.VALID_INTENTS
        )

    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "IntentResolver",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),

            "intent_count":
                len(
                    self.VALID_INTENTS
                ),
        }


__all__ = [
    "IntentResolver",
]
