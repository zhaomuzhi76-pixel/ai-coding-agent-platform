from __future__ import annotations

from backend.core.context.execution_variable import (
    ExecutionVariable,
)

from backend.core.context.execution_variable_contract import (
    ExecutionVariableSnapshot,
)

from backend.core.context.execution_variable_store_contract import (
    ExecutionVariableStoreSnapshot,
)


class ExecutionVariableStore:
    """
    Execution variable entity store.

    Responsibility:

        - store execution variables
        - query execution variables
        - remove execution variables
        - expose variable store snapshot

    Not Responsible:

        - persistence
        - variable business logic
        - lifecycle
        - scheduling
    """

    VERSION = "3.0"

    RESPONSIBILITY = (
        "execution_variable_storage",
    )

    def __init__(
        self,
    ) -> None:

        self._variables: dict[
            str,
            ExecutionVariable,
        ] = {}

    def add(
        self,
        variable: ExecutionVariable,
    ) -> None:

        if not isinstance(
            variable,
            ExecutionVariable,
        ):
            raise TypeError(
                "variable must be ExecutionVariable"
            )

        if variable.name in self._variables:
            raise ValueError(
                f"variable already exists: {variable.name}"
            )

        self._variables[
            variable.name
        ] = variable

    def get(
        self,
        name: str,
    ) -> ExecutionVariable | None:

        return self._variables.get(
            name
        )

    def exists(
        self,
        name: str,
    ) -> bool:

        return name in self._variables

    def remove(
        self,
        name: str,
    ) -> None:

        self._variables.pop(
            name,
            None,
        )

    def clear(
        self,
    ) -> None:

        self._variables.clear()

    def count(
        self,
    ) -> int:

        return len(
            self._variables
        )

    def ready(
        self,
    ) -> bool:

        return isinstance(
            self._variables,
            dict,
        )

    def names(
        self,
    ) -> tuple[str, ...]:

        return tuple(
            self._variables.keys()
        )


    def snapshot(
        self,
    ) -> dict[
        str,
        ExecutionVariableSnapshot,
    ]:

        return {
            name: variable.dump()
            for name, variable
            in self._variables.items()
        }

    def dump(
        self,
    ) -> ExecutionVariableStoreSnapshot:

        return {
            "name": "ExecutionVariableStore",
            "version": self.VERSION,
            "responsibility": self.RESPONSIBILITY,
            "ready": self.ready(),
            "count": self.count(),
            "variables": self.snapshot(),
        }


__all__ = [
    "ExecutionVariableStore",
]
