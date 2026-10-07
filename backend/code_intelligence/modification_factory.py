from __future__ import annotations

from typing import Any

from backend.code_intelligence.modification_pipeline import (
    ModificationPipeline,
)
from backend.code_intelligence.modification_planner import (
    ModificationPlanner,
)
from backend.code_intelligence.modification_workflow import (
    ModificationWorkflow,
)
from backend.code_intelligence.patch_backup import (
    PatchBackup,
)
from backend.code_intelligence.patch_executor import (
    PatchExecutor,
)
from backend.code_intelligence.patch_generator import (
    PatchGenerator,
)
from backend.code_intelligence.patch_rollback import (
    PatchRollback,
)
from backend.code_intelligence.patch_validator import (
    PatchValidator,
)
from backend.code_intelligence.patch_writer import (
    PatchWriter,
)
from backend.code_intelligence.syntax_checker import (
    SyntaxChecker,
)
from backend.code_intelligence.test_executor import (
    TestExecutor,
)
from backend.code_intelligence.verification_runner import (
    VerificationRunner,
)

class ModificationFactory:
    """
    Compose the transactional modification execution chain.

    Construction only; business execution belongs to workflow.
    """

    VERSION = "11.0"
    RESPONSIBILITY = (
        "transactional_code_modification_factory",
    )

    def __init__(
        self,
        planner: Any | None = None,
        patch_generator: Any | None = None,
        patch_executor: Any | None = None,
        verifier: Any | None = None,
        rollback: Any | None = None,
    ) -> None:
        writer = PatchWriter()
        validator = PatchValidator()
        backup = PatchBackup()

        self.planner = (
            planner or ModificationPlanner()
        )
        self.patch_generator = (
            patch_generator or PatchGenerator()
        )
        self.patch_executor = (
            patch_executor
            or PatchExecutor(
                writer=writer,
                validator=validator,
                backup=backup,
            )
        )
        self.verifier = (
            verifier
            or VerificationRunner(
                syntax_checker=SyntaxChecker(),
                test_executor=TestExecutor(),
            )
        )
        self.rollback = (
            rollback or PatchRollback()
        )

    def create_workflow(
        self,
    ) -> ModificationWorkflow:
        return ModificationWorkflow(
            planner=self.planner,
            patch_generator=self.patch_generator,
            patch_executor=self.patch_executor,
            verifier=self.verifier,
            rollback=self.rollback,
        )

    def create_pipeline(
        self,
    ) -> ModificationPipeline:
        return ModificationPipeline(
            workflow=self.create_workflow()
        )

    def ready(self) -> bool:
        return all(
            (
                self.planner is not None,
                self.patch_generator is not None,
                self.patch_executor is not None,
                self.verifier is not None,
                self.rollback is not None,
            )
        )

    def dump(self) -> dict[str, Any]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "components": {
                "planner": type(
                    self.planner
                ).__name__,
                "patch_generator": type(
                    self.patch_generator
                ).__name__,
                "patch_executor": type(
                    self.patch_executor
                ).__name__,
                "verifier": type(
                    self.verifier
                ).__name__,
                "rollback": type(
                    self.rollback
                ).__name__,
            },
        }

__all__ = [
    "ModificationFactory",
]
