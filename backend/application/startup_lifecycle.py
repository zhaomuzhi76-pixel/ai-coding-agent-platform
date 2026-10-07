from __future__ import annotations

from typing import Any

from backend.application.startup_accessors import ApplicationStartupAccessors
from backend.application.startup_support import ApplicationStartupSupport


class ApplicationStartupLifecycle:
    """
    Lifecycle implementation delegated by ApplicationStartup.

    Owns:
        - strict start/stop state transitions
        - start sequencing
        - assembled-state validation
        - readiness projection
        - failure rollback cleanup
        - application-owned Agent shutdown orchestration
    """

    VERSION = "1.3"

    def __init__(
        self,
        owner: Any,
        accessors: ApplicationStartupAccessors,
    ) -> None:
        self.owner = owner
        self.accessors = accessors

    def start(self) -> None:
        if self.accessors.started(self.owner.state):
            raise RuntimeError(
                "application startup already started"
            )

        try:
            result = self.owner.assembly.build(
                registry=self.owner.registry,
                capability_composition=self.owner.capability_composition,
                planning_binding=self.owner.planning_binding,
                code_intelligence_binding=self.owner.code_intelligence_binding,
                tool_binding=self.owner.tool_binding,
                project_session_composition=self.owner.project_session_composition,
                project_session_operational=self.owner.project_session_operational,
                project_session_binding=self.owner.project_session_binding,
                project_registry=self.owner.project_registry,
                project_registration=self.owner.project_registration,
                planner=self.owner.planner,
            )
            self.owner.state.commit(result)
            self.owner.registry.start()

            if not self.assembled():
                raise RuntimeError(
                    "application assembly unavailable"
                )

            self.owner.state.started = True

            if not self.ready():
                raise RuntimeError(
                    "application startup unavailable"
                )

        except Exception:
            self._cleanup()
            raise

    def assembled(self) -> bool:
        return ApplicationStartupSupport.assembled(
            registry=self.accessors.registry(self.owner),
            runtime=self.accessors.runtime(self.owner.state),
            agent_service=self.accessors.agent_service(
                self.owner.state
            ),
            capability_manager=self.accessors.capability_manager(
                self.owner.state
            ),
            agent_capability_key=(
                self.owner.capability_composition.AGENT_DESCRIPTOR.key()
            ),
            planning_binding=self.owner.planning_binding,
            planning_capability_key=(
                self.owner.planning_binding.CAPABILITY_KEY
            ),
            code_intelligence_binding=(
                self.owner.code_intelligence_binding
            ),
            code_intelligence_capability_key=(
                self.owner.code_intelligence_binding.CAPABILITY_KEY
            ),
            tool_binding=self.owner.tool_binding,
            tool_capability_key=(
                self.owner.tool_binding.CAPABILITY_KEY
            ),
        )

    def ready(self) -> bool:
        state = self.owner.state
        return (
            state.started
            and self.owner.assembly.ready()
            and self.assembled()
            and state.runtime_submission is not None
            and state.runtime_submission.ready()
            and self.owner.project_session_binding.ready()
            and state.ready()
        )

    def stop(self) -> None:
        if not self.accessors.started(self.owner.state):
            return
        self._cleanup()

    def _cleanup(self) -> None:
        self.owner.project_session_binding.stop()

        manager = self.owner.state.capability_manager
        if manager is not None:
            for key in (
                self.owner.tool_binding.CAPABILITY_KEY,
                self.owner.code_intelligence_binding.CAPABILITY_KEY,
                self.owner.planning_binding.CAPABILITY_KEY,
                self.owner.capability_composition.AGENT_DESCRIPTOR.key(),
            ):
                ApplicationStartupSupport.unload(
                    manager,
                    ApplicationStartupSupport._capability_name(
                        key
                    ),
                )

        self.owner.tool_binding.reset()
        self.owner.code_intelligence_binding.reset()
        self.owner.planning_binding.reset()
        self.owner.registry.stop()
        self.owner.state.clear()

    def dump(self) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
            "started": self.owner.state.started,
        }


__all__ = [
    "ApplicationStartupLifecycle",
]
