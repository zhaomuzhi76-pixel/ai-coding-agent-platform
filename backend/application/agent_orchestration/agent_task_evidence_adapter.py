from __future__ import annotations

from typing import Any

from backend.application.agent_orchestration.agent_task_evidence import (
    AgentTaskEvidence,
)
from backend.core.result import ExecutionResult


class AgentTaskEvidenceAdapter:
    """
    Project canonical execution results into task evidence.

    Owns:
        - execution fact projection
        - output-count projection
        - verification fact extraction
        - code-modification result extraction

    Does not own:
        - verification execution
        - task acceptance
        - completion decision
        - orchestration decision
    """

    VERSION = "1.1"
    VERIFICATION_KEY = "verification_success"
    MODIFICATION_KEY = "modification_result"

    def adapt(
        self,
        *,
        result: ExecutionResult,
    ) -> AgentTaskEvidence:
        self._validate(result)

        modification = self._find_modification(
            result.outputs
        )

        verification = self._verification(
            result,
            modification,
        )

        metadata: dict[str, object] = {
            "model": result.model,
        }

        if modification is not None:
            metadata[self.MODIFICATION_KEY] = (
                modification
            )

        return AgentTaskEvidence(
            execution_success=result.success,
            output_count=result.count(),
            verification_success=verification,
            orchestration_signal=self._signal(result),
            metadata=metadata,
        )

    @classmethod
    def _verification(
        cls,
        result: ExecutionResult,
        modification: dict[str, Any] | None,
    ) -> bool | None:
        value = result.metadata.get(
            cls.VERIFICATION_KEY
        )

        if value is not None:
            if not isinstance(value, bool):
                raise TypeError(
                    "verification_success must bool"
                )
            return value

        if modification is None:
            return None

        pipeline = modification.get(
            "pipeline"
        )

        if not isinstance(pipeline, dict):
            return None

        nested = pipeline.get("result")

        if not isinstance(nested, dict):
            return None

        value = nested.get("verification")

        if not isinstance(value, dict):
            return None

        success = value.get("success")

        if success is None:
            return None

        if not isinstance(success, bool):
            raise TypeError(
                "modification verification success "
                "must bool"
            )

        return success

    @classmethod
    def _find_modification(
        cls,
        outputs: list[object],
    ) -> dict[str, Any] | None:
        for output in outputs:
            found = cls._find_mapping(output)

            if found is not None:
                return found

        return None

    @classmethod
    def _find_mapping(
        cls,
        value: object,
    ) -> dict[str, Any] | None:
        if isinstance(value, dict):
            if cls._is_modification(value):
                return value

            for nested in value.values():
                found = cls._find_mapping(nested)

                if found is not None:
                    return found

        elif isinstance(value, list):
            for item in value:
                found = cls._find_mapping(item)

                if found is not None:
                    return found

        return None

    @staticmethod
    def _is_modification(
        value: dict[str, Any],
    ) -> bool:
        return (
            isinstance(
                value.get("file"),
                str,
            )
            and isinstance(
                value.get("replacement"),
                str,
            )
            and isinstance(
                value.get("pipeline"),
                dict,
            )
        )

    @staticmethod
    def _signal(
        result: ExecutionResult,
    ) -> str | None:
        value = result.metadata.get(
            "orchestration_decision"
        )

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(
                "orchestration_decision must str"
            )

        value = value.strip().lower()

        if value not in (
            "completed",
            "continue",
            "replan",
            "failed",
        ):
            raise ValueError(
                "unsupported orchestration decision"
            )

        return value

    @staticmethod
    def _validate(
        result: ExecutionResult,
    ) -> None:
        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "execution result required"
            )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "verification_key": self.VERIFICATION_KEY,
            "modification_key": self.MODIFICATION_KEY,
        }


__all__ = [
    "AgentTaskEvidenceAdapter",
]
