from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentTaskEvidence:
    """
    Application evidence contract for task acceptance.

    Owns:
        - execution success fact
        - produced-output fact
        - verification fact
        - explicit orchestration signal

    Does not own:
        - task goal
        - execution
        - planning
        - decision construction
    """

    execution_success: bool
    output_count: int
    verification_success: bool | None = None
    orchestration_signal: str | None = None
    metadata: dict[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.execution_success,
            bool,
        ):
            raise TypeError(
                "execution_success must bool"
            )

        if (
            not isinstance(
                self.output_count,
                int,
            )
            or self.output_count < 0
        ):
            raise ValueError(
                "output_count must be >= 0"
            )

        if (
            self.verification_success is not None
            and not isinstance(
                self.verification_success,
                bool,
            )
        ):
            raise TypeError(
                "verification_success must bool or None"
            )

        if (
            self.orchestration_signal is not None
            and not isinstance(
                self.orchestration_signal,
                str,
            )
        ):
            raise TypeError(
                "orchestration_signal must str or None"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    def ready(self) -> bool:
        return True

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "execution_success": self.execution_success,
            "output_count": self.output_count,
            "verification_success": self.verification_success,
            "orchestration_signal": (
                self.orchestration_signal
            ),
            "metadata": dict(self.metadata),
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskEvidence",
]
