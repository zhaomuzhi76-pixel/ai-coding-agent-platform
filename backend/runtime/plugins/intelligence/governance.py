from __future__ import annotations


class IntelligenceGovernanceService:
    """
    Intelligence decision boundary.

    Responsibility:
        - decide whether experience should persist
        - normalize intelligence signals

    Not Responsible:
        - storage
        - embedding
        - retrieval
        - session management
    """

    VERSION = "1.0"

    def should_persist(
        self,
        signal: object,
    ) -> bool:
        return signal is not None

    def normalize(
        self,
        signal: object,
    ) -> dict[str, object]:
        return {
            "signal": signal,
            "persist": self.should_persist(
                signal
            ),
        }

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "IntelligenceGovernanceService",
]
