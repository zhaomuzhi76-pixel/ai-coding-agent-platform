from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.application.agent_orchestration.agent_task_goal import (
    AgentTaskGoal,
)
from backend.application.agent_orchestration.agent_task_objective_evidence import (
    AgentTaskObjectiveEvidence,
)
from backend.application.agent_orchestration.agent_task_objective_fact import (
    AgentTaskObjectiveFact,
)


class AgentTaskModificationEvidenceProjector:
    """
    Project a real code-modification result into objective facts.

    Expected input is the result returned by the modification
    execution provider:

        {
            "success": bool,
            "file": "...",
            "replacement": "...",
            "pipeline": {
                "result": {
                    "execution": [...],
                    "verification": {...}
                }
            }
        }

    Owns:
        - extract modification target and replacement
        - read actual target content
        - create objective facts

    Does not own:
        - file modification
        - verification execution
        - acceptance
        - completion
        - orchestration decision
    """

    VERSION = "1.0"

    def project(
        self,
        *,
        goal: AgentTaskGoal,
        modification: dict[str, Any],
    ) -> AgentTaskObjectiveEvidence:
        self._validate(
            goal,
            modification,
        )

        execution = self._execution(
            modification,
        )

        if not execution:
            return AgentTaskObjectiveEvidence()

        target = execution.get(
            "target"
        ) or modification.get(
            "file"
        )

        replacement = modification.get(
            "replacement"
        )

        if (
            not isinstance(target, str)
            or not target.strip()
        ):
            return AgentTaskObjectiveEvidence()

        if not isinstance(
            replacement,
            str,
        ):
            return AgentTaskObjectiveEvidence()

        path = Path(target)

        if not path.is_absolute():
            path = (
                Path(goal.workspace).expanduser().resolve()
                / path
            ).resolve()

        if not path.is_file():
            return AgentTaskObjectiveEvidence()

        actual = path.read_text(
            encoding="utf-8"
        )

        return AgentTaskObjectiveEvidence(
            facts=(
                AgentTaskObjectiveFact(
                    key="modified_file_content",
                    expected=replacement,
                    actual=actual,
                    source="code_modification_verification",
                ),
            )
        )

    @staticmethod
    def _execution(
        modification: dict[str, Any],
    ) -> dict[str, Any]:
        pipeline = modification.get(
            "pipeline"
        )

        if not isinstance(
            pipeline,
            dict,
        ):
            return {}

        result = pipeline.get(
            "result"
        )

        if not isinstance(
            result,
            dict,
        ):
            return {}

        execution = result.get(
            "execution"
        )

        if not isinstance(
            execution,
            list,
        ) or not execution:
            return {}

        item = execution[0]

        return (
            item
            if isinstance(item, dict)
            else {}
        )

    @staticmethod
    def _validate(
        goal: AgentTaskGoal,
        modification: dict[str, Any],
    ) -> None:
        if not isinstance(
            goal,
            AgentTaskGoal,
        ):
            raise TypeError(
                "task goal required"
            )

        if not isinstance(
            modification,
            dict,
        ):
            raise TypeError(
                "modification result required"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskModificationEvidenceProjector",
]
