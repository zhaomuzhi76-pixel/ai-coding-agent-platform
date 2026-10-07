from __future__ import annotations

from typing import Any

from backend.agent.planner.builder_registry import BuilderRegistry
from backend.agent.planner.intent_resolver import IntentResolver
from backend.agent.planner.llm_intent_classifier import LLMIntentClassifier
from backend.agent.planner.plan_builder import PlanBuilder
from backend.agent.planner.plan_composer import PlanComposer
from backend.agent.planner.plan_context_factory import PlanContextFactory
from backend.agent.planner.task_analyzer import TaskAnalyzer
from backend.agent.planner.models.planner_intent import PlannerIntent
from backend.agent.planner.models.task_plan import TaskPlan
from backend.core.planning.intelligence_port import PlannerIntelligenceProtocol


_INTENT_FALLBACK = {
    "create_project": "text_generate",
}


class PlannerEngine:
    VERSION = "6.0"
    RESPONSIBILITY = ("planner_orchestration_engine",)

    UNDERSTAND_HINTS = (
        "做什么", "干什么", "介绍", "优势", "短板", "优缺点",
        "设计理念", "设计思路", "任务是", "目标是", "用来",
        "整体介绍", "简述", "分析这个", "分析整个",
    )

    ERROR_HINTS = (
        "Traceback (most recent call last)",
        "SyntaxError:", "IndentationError:",
        "NameError:", "KeyError:", "AttributeError:",
        "TypeError:", "ValueError:", "ImportError:",
        "ModuleNotFoundError:", "AssertionError:",
        "FAILED ",
    )

    def __init__(
        self,
        analyzer: TaskAnalyzer | None = None,
        resolver: IntentResolver | None = None,
        builder: PlanBuilder | None = None,
        composer: PlanComposer | None = None,
        intelligence: PlannerIntelligenceProtocol | None = None,
        llm_classifier: LLMIntentClassifier | None = None,
    ) -> None:
        self.analyzer = analyzer or TaskAnalyzer()
        self.resolver = resolver or IntentResolver()
        self.builder = (
            builder
            or PlanBuilder(
                builder_registry=BuilderRegistry(),
                context_factory=PlanContextFactory(),
            )
        )
        self.composer = composer or PlanComposer()
        self.intelligence = intelligence
        self.llm_classifier = llm_classifier or LLMIntentClassifier()
        self.created_count = 0
        self.llm_intent_count = 0

    async def create_plan(
        self,
        message: str,
        workspace: str = ".",
        model: str | None = None,
    ) -> TaskPlan:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("planner message required")
        if not isinstance(workspace, str) or not workspace.strip():
            raise ValueError("planner workspace required")

        intent = self._detect_prefix_intent(message)

        if intent is None:
            analysis = self.analyzer.analyze(message)
            intent = self.resolver.resolve(analysis)
            if intent.name == "text_generate" and model:
                intent = await self._llm_fallback(message, model, intent)

        context = dict(intent.parameters)
        context["workspace"] = workspace
        context["message"] = message

        if self.intelligence is not None:
            context["project_context"] = (
                self.intelligence.project_intelligence()
            )

        steps = self.builder.build(
            intent=intent, context=context, message=message,
        )
        steps = self.composer.compose(steps)

        plan = TaskPlan.create(
            goal=message, workspace=workspace, model=model, steps=steps,
        )
        self.created_count += 1
        return plan

    def _detect_prefix_intent(
        self, message: str,
    ) -> PlannerIntent | None:
        if any(h in message for h in self.ERROR_HINTS):
            print(f"[planner] fix_error 前置命中: {message[:60]!r}",
                  flush=True)
            return PlannerIntent(
                name="fix_error",
                parameters={"message": message, "raw_error": message},
                capabilities=[],
                complexity="simple",
                risk_level="medium",
            )
        if any(h in message.lower() for h in self.UNDERSTAND_HINTS):
            print(f"[planner] understand_project 前置命中: {message!r}",
                  flush=True)
            return PlannerIntent(
                name="understand_project",
                parameters={"message": message},
                capabilities=[],
                complexity="simple",
                risk_level="low",
            )
        return None

    async def _llm_fallback(
        self, message: str, model: str, fallback: PlannerIntent,
    ) -> PlannerIntent:
        try:
            llm_result = await self.llm_classifier.classify(
                message=message, model=model,
            )
            detected = llm_result["intent"]
            params = llm_result["parameters"]
            if detected != "text_generate":
                self.llm_intent_count += 1
                exec_name = _INTENT_FALLBACK.get(detected, detected)
                print(f"[planner-llm-intent] message={message!r} "
                      f"detected={detected!r} exec={exec_name!r} "
                      f"params={params}", flush=True)
                return PlannerIntent(
                    name=exec_name,
                    parameters={
                        **dict(fallback.parameters),
                        **params,
                        "_llm_detected": detected,
                    },
                    capabilities=list(fallback.capabilities),
                    complexity=fallback.complexity,
                    risk_level=fallback.risk_level,
                )
        except Exception as error:
            print(f"[planner-llm-intent] fallback failed: "
                  f"{type(error).__name__}: {error}", flush=True)
        return fallback

    def ready(self) -> bool:
        return all((
            self.analyzer, self.resolver, self.builder, self.composer,
            self.intelligence is None or self.intelligence.ready(),
        ))

    def dump(self) -> dict[str, Any]:
        return {
            "name": type(self).__name__, "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "created_count": self.created_count,
            "llm_intent_count": self.llm_intent_count,
            "intelligence": (
                type(self.intelligence).__name__
                if self.intelligence is not None else None
            ),
            "builder": self.builder.dump(),
            "llm_classifier": self.llm_classifier.dump(),
        }


__all__ = ["PlannerEngine"]
