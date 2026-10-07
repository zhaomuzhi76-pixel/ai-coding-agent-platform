from __future__ import annotations

from backend.core.agent.agent_request import AgentRequest
from backend.core.errors import CoreErrorDetail
from backend.core.result import (
    ExecutionResult,
    ResultOutput,
    ResultSerializer,
    is_result_value,
)
from backend.runtime.contracts.execution import NodeExecutionResult


class RuntimeResultFactory:
    """
    Runtime execution result creation boundary.

    Responsibility:
        - validate runtime execution outputs
        - normalize runtime-owned values into core ResultValue
        - create the stable core ExecutionResult

    Not Responsible:
        - core result ownership
        - execution
        - result processing
        - transport
        - persistence
    """

    VERSION = "7.0"

    RESPONSIBILITY = (
        "execution_result_creation_boundary",
        "runtime_to_core_result_normalization",
    )

    def create(
        self,
        *,
        outputs: list[object],
        request: AgentRequest,
    ) -> ExecutionResult:
        self._validate_request(request)
        self._validate_outputs(outputs)

        failures = self._failed_results(outputs)
        normalized_outputs = [
            self._normalize_output(output)
            for output in outputs
        ]

        return ExecutionResult(
            outputs=normalized_outputs,
            final=self._build_final(normalized_outputs),
            model=request.model,
            success=not bool(failures),
            error=self._build_error(failures),
            metadata=self._build_metadata(
                request,
                failures,
            ),
        )

    def ready(
        self,
    ) -> bool:
        return ResultSerializer.ready()

    def dump(
        self,
    ) -> dict[str, object]:
        return {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "serializer": ResultSerializer.dump(),
        }

    def _normalize_output(
        self,
        output: object,
    ) -> ResultOutput:
        if isinstance(output, NodeExecutionResult):
            return ResultSerializer.to_dict(output)

        if is_result_value(output):
            return output

        return ResultSerializer.to_dict(output)

    def _build_final(
        self,
        outputs: list[ResultOutput],
    ) -> ResultOutput | None:
        if not outputs:
            return None

        if len(outputs) == 1:
            return outputs[0]

        return list(outputs)

    def _build_error(
        self,
        failures: list[NodeExecutionResult],
    ) -> CoreErrorDetail | None:
        if not failures:
            return None

        error = failures[0].error

        if not isinstance(error, CoreErrorDetail):
            raise TypeError(
                "failed node result must contain "
                "CoreErrorDetail"
            )

        return error

    def _build_metadata(
        self,
        request: AgentRequest,
        failures: list[NodeExecutionResult],
    ) -> dict[str, object]:
        metadata: dict[str, object] = {
            "model": request.model,
        }

        if failures:
            metadata.update(
                {
                    "failure_count": len(failures),
                    "failed_node_ids": [
                        result.node_id
                        for result in failures
                    ],
                }
            )

        return metadata

    @staticmethod
    def _failed_results(
        outputs: list[object],
    ) -> list[NodeExecutionResult]:
        return [
            output
            for output in outputs
            if isinstance(output, NodeExecutionResult)
            and not output.success
        ]

    @staticmethod
    def _validate_request(
        request: AgentRequest,
    ) -> None:
        if not isinstance(request, AgentRequest):
            raise TypeError(
                "result request must AgentRequest"
            )

        if not request.ready():
            raise ValueError(
                "result request not ready"
            )

    @staticmethod
    def _validate_outputs(
        outputs: list[object],
    ) -> None:
        if not isinstance(outputs, list):
            raise TypeError(
                "result outputs must list"
            )

        for output in outputs:
            if isinstance(output, NodeExecutionResult):
                if not output.ready():
                    raise ValueError(
                        "node execution result not ready"
                    )
                continue

            if not is_result_value(output):
                normalized = ResultSerializer.to_dict(
                    output
                )

                if not is_result_value(normalized):
                    raise TypeError(
                        "serialized runtime result "
                        "is not ResultValue"
                    )


__all__ = [
    "RuntimeResultFactory",
]
