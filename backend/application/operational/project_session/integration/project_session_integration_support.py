from __future__ import annotations

from backend.application.runtime_execution_gateway import (
    ApplicationRuntimeExecutionGatewayContract,
)
from backend.application.operational.project_session.project_session_operational_contract import (
    ProjectSessionOperationalContract,
)
from backend.core.result import ExecutionResult


class ProjectSessionIntegrationSupport:
    """
    Shared validation support for project-session integration bridges.

    Owns:
        - operational validation
        - canonical execution-gateway validation
        - generic downstream-target validation
        - session-id validation
        - execution-result validation

    Does not own:
        - execution
        - lifecycle mutation
        - construction
        - transport
    """

    VERSION = "2.0"

    @staticmethod
    def validate_operational(
        operational: object,
    ) -> ProjectSessionOperationalContract:
        if not isinstance(
            operational,
            ProjectSessionOperationalContract,
        ):
            raise TypeError(
                "operational must implement "
                "ProjectSessionOperationalContract"
            )

        if not operational.ready():
            raise RuntimeError(
                "project session operational not ready"
            )

        return operational

    @staticmethod
    def validate_execution_gateway(
        gateway: object,
    ) -> ApplicationRuntimeExecutionGatewayContract:
        if not isinstance(
            gateway,
            ApplicationRuntimeExecutionGatewayContract,
        ):
            raise TypeError(
                "execution gateway must implement "
                "ApplicationRuntimeExecutionGatewayContract"
            )

        if not gateway.ready():
            raise RuntimeError(
                "execution gateway not ready"
            )

        return gateway

    @staticmethod
    def validate_target(
        target: object,
        name: str,
    ) -> object:
        if target is None:
            raise ValueError(
                f"{name} required"
            )

        execute = getattr(
            target,
            "execute",
            None,
        )
        ready = getattr(
            target,
            "ready",
            None,
        )

        if not callable(execute):
            raise TypeError(
                f"{name} must expose execute()"
            )

        if not callable(ready):
            raise TypeError(
                f"{name} must expose ready()"
            )

        if not ready():
            raise RuntimeError(
                f"{name} not ready"
            )

        return target

    @staticmethod
    def validate_session(
        session_id: object,
    ) -> str:
        if not isinstance(
            session_id,
            str,
        ):
            raise TypeError(
                "session id must str"
            )

        value = session_id.strip()

        if not value:
            raise ValueError(
                "session id required"
            )

        return value

    @staticmethod
    def validate_result(
        result: object,
    ) -> ExecutionResult:
        if not isinstance(
            result,
            ExecutionResult,
        ):
            raise TypeError(
                "integration target must return "
                "ExecutionResult"
            )

        if not result.ready():
            raise RuntimeError(
                "execution result not ready"
            )

        return result

    def ready(
        self,
    ) -> bool:
        return True

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": type(self).__name__,
            "version": self.VERSION,
            "ready": self.ready(),
        }


__all__ = [
    "ProjectSessionIntegrationSupport",
]
