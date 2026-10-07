from __future__ import annotations

from collections import deque

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


class RuntimeGraphCycleValidator:
    """
    Runtime graph cycle validator.

    Responsibility:
        - detect dependency cycles

    Not Responsible:
        - dependency existence
        - topology generation
        - execution
        - scheduling
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "runtime_graph_cycle_validation",
    )


    def validate(
        self,
        graph: RuntimeGraph,
    ) -> bool:

        if not isinstance(
            graph,
            RuntimeGraph,
        ):
            raise TypeError(
                "graph must RuntimeGraph"
            )

        self._validate_cycle(
            graph
        )

        return True


    def _validate_cycle(
        self,
        graph: RuntimeGraph,
    ) -> None:

        indegree: dict[str, int] = {
            node_id: 0
            for node_id in graph.node_ids()
        }


        children: dict[str, list[str]] = {
            node_id: []
            for node_id in graph.node_ids()
        }


        for node in graph.all_nodes():

            for dependency in node.depends_on:

                indegree[
                    node.node_id
                ] += 1


                children[
                    dependency
                ].append(
                    node.node_id
                )


        queue = deque(
            [
                node_id
                for node_id, degree
                in indegree.items()
                if degree == 0
            ]
        )


        visited = 0


        while queue:

            current = queue.popleft()

            visited += 1


            for child in children[current]:

                indegree[child] -= 1


                if indegree[child] == 0:
                    queue.append(
                        child
                    )


        if visited != graph.node_count():

            raise ValueError(
                "runtime graph contains cycle"
            )


    def ready(
        self,
    ) -> bool:

        return True


    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": (
                "RuntimeGraphCycleValidator"
            ),
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeGraphCycleValidator",
]
