from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentTaskObjectiveFact:
    """
    Objective fact extracted from task execution evidence.

    Owns:
        - objective key
        - expected value
        - actual value
        - evidence source

    Does not own:
        - execution
        - verification execution
        - completion decision
        - loop control
    """

    key: str
    expected: str
    actual: str
    source: str

    def __post_init__(self) -> None:
        for name, value in (
            ("key", self.key),
            ("expected", self.expected),
            ("actual", self.actual),
            ("source", self.source),
        ):
            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(
                    f"{name} required"
                )

    @property
    def matched(self) -> bool:
        return self.expected.strip() == self.actual.strip()

    def ready(self) -> bool:
        return all(
            isinstance(value, str)
            and bool(value.strip())
            for value in (
                self.key,
                self.expected,
                self.actual,
                self.source,
            )
        )

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "source": self.source,
            "matched": self.matched,
            "ready": self.ready(),
        }


__all__ = [
    "AgentTaskObjectiveFact",
]
