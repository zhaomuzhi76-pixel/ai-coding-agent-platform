from __future__ import annotations

from typing import Any

from backend.application.agent_orchestration.agent_task_evidence import (
    AgentTaskEvidence,
)
from backend.application.agent_orchestration.agent_task_goal import (
    AgentTaskGoal,
)
from backend.application.agent_orchestration.agent_task_modification_evidence_projector import (
    AgentTaskModificationEvidenceProjector,
)
from backend.application.agent_orchestration.agent_task_objective_evidence import (
    AgentTaskObjectiveEvidence,
)
from backend.application.agent_orchestration.agent_task_objective_fact import (
    AgentTaskObjectiveFact,
)


class AgentTaskObjectiveEvidenceAdapter:
    """
    Project structured task metadata into objective evidence.

    Supported structured metadata:
        objective_facts=[
            {
                "key": "...",
                "expected": "...",
                "actual": "...",
                "source": "..."
            }
        ]

    No structured facts means objective achievement is unproven.
    """

    VERSION = "1.0"
    FACTS_KEY = "objective_facts"

    def adapt(
        self,
        *,
        goal: AgentTaskGoal,
        evidence: AgentTaskEvidence,
    ) -> AgentTaskObjectiveEvidence:
        self._validate(
            goal,
            evidence,
        )

        modification = evidence.metadata.get(
            "modification_result"
        )

        if isinstance(
            modification,
            dict,
        ):
            return AgentTaskModificationEvidenceProjector().project(
                goal=goal,
                modification=modification,
            )

        raw = evidence.metadata.get(
            self.FACTS_KEY
        )

        if raw is None:
            return AgentTaskObjectiveEvidence()

        if not isinstance(raw, list):
            raise TypeError(
                "objective_facts must list"
            )

        facts = []

        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                raise TypeError(
                    f"objective_facts[{index}] must dict"
                )

            facts.append(
                AgentTaskObjectiveFact(
                    key=self._string(
                        item,
                        "key",
                    ),
                    expected=self._string(
                        item,
                        "expected",
                    ),
                    actual=self._string(
                        item,
                        "actual",
                    ),
                    source=self._string(
                        item,
                        "source",
                    ),
                )
            )

        return AgentTaskObjectiveEvidence(
            facts=tuple(facts)
        )

    @staticmethod
    def _string(
        item: dict[str, Any],
        key: str,
    ) -> str:
        value = item.get(key)

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise ValueError(
                f"objective fact {key} required"
            )

        return value.strip()

    @staticmethod
    def _validate(
        goal: AgentTaskGoal,
        evidence: AgentTaskEvidence,
    ) -> None:
        if not isinstance(
            goal,
            AgentTaskGoal,
        ):
            raise TypeError(
                "task goal required"
            )

        if not isinstance(
            evidence,
            AgentTaskEvidence,
        ):
            raise TypeError(
                "task evidence required"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "facts_key": self.FACTS_KEY,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskObjectiveEvidenceAdapter",
]
