from __future__ import annotations

from backend.core.context.execution_output import (
    ExecutionOutput,
)

from backend.core.context.execution_output_contract import (
    ExecutionOutputSnapshot,
)

from backend.core.context.execution_output_store_contract import (
    ExecutionOutputStoreSnapshot,
)


class ExecutionOutputStore:
    """
    Execution output entity store.

    Responsibility:

        - store execution outputs
        - query execution outputs
        - remove execution outputs
        - expose output store snapshot

    Not Responsible:

        - output generation
        - payload processing
        - artifact management
        - persistence
        - lifecycle
        - scheduling
    """

    VERSION = "4.0"

    RESPONSIBILITY = (
        "execution_output_storage",
    )

    def __init__(
        self,
    ) -> None:

        self._outputs: dict[
            str,
            ExecutionOutput,
        ] = {}

    def add(
        self,
        output: ExecutionOutput,
    ) -> None:

        if not isinstance(
            output,
            ExecutionOutput,
        ):
            raise TypeError(
                "output must be ExecutionOutput"
            )

        if output.name in self._outputs:
            raise ValueError(
                f"output already exists: {output.name}"
            )

        self._outputs[
            output.name
        ] = output

    def get(
        self,
        name: str,
    ) -> ExecutionOutput | None:

        return self._outputs.get(
            name
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._outputs

    def remove(
        self,
        name: str,
    ) -> None:

        self._outputs.pop(
            name,
            None,
        )

    def clear(
        self,
    ) -> None:

        self._outputs.clear()

    def count(
        self,
    ) -> int:

        return len(
            self._outputs
        )

    def ready(
        self,
    ) -> bool:

        return isinstance(
            self._outputs,
            dict,
        )

    def names(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._outputs.keys()
        )


    def snapshot(
        self,
    ) -> dict[
        str,
        ExecutionOutputSnapshot,
    ]:

        return {
            name: output.dump()
            for name, output
            in self._outputs.items()
        }

    def dump(
        self,
    ) -> ExecutionOutputStoreSnapshot:

        return {
            "name": "ExecutionOutputStore",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "count": self.count(),
            "outputs": self.snapshot(),
        }


__all__ = [
    "ExecutionOutputStore",
]
