from __future__ import annotations

from typing import Any

from backend.agent.graph.task_graph import TaskGraph


class GraphValidator:
    """
    Validate runtime DAG structure.

    Responsibility:
        - dependency validation
        - cycle detection
        - graph contract validation

    Not Responsible:
        - execution
        - scheduling
        - lifecycle
        - persistence
    """

    VERSION = "5.0"

    RESPONSIBILITY = (
        "dag_structure_validation",
    )

    def validate(
        self,
        graph: TaskGraph,
    ) -> dict[str, Any]:

        if graph is None:
            return {
                "valid": False,
                "errors": [
                    "graph required"
                ],
            }

        errors = []

        errors.extend(
            self._missing_dependencies(
                graph
            )
        )

        if self.has_cycle(graph):
            errors.append(
                "cycle detected"
            )

        return {
            "valid": not errors,
            "errors": errors,
        }


    def _missing_dependencies(
        self,
        graph: TaskGraph,
    ) -> list[str]:

        errors: list[str] = []

        node_ids = {
            node.node_id
            for node in graph.all_nodes()
        }

        for node in graph.all_nodes():

            for dependency in node.depends_on:

                if dependency not in node_ids:
                    errors.append(
                        (
                            "missing dependency:"
                            f"{dependency}"
                            f" for node:{node.node_id}"
                        )
                    )

        return errors


    def has_cycle(
        self,
        graph: TaskGraph,
    ) -> bool:

        visited: set[str] = set()
        active: set[str] = set()


        def visit(
            node_id: str,
        ) -> bool:

            if node_id in active:
                return True

            if node_id in visited:
                return False

            visited.add(
                node_id
            )

            active.add(
                node_id
            )

            node = graph.get_node(
                node_id
            )

            if node:

                for dependency in node.depends_on:

                    if visit(
                        dependency
                    ):
                        return True

            active.remove(
                node_id
            )

            return False


        for node in graph.all_nodes():

            if visit(
                node.node_id
            ):
                return True

        return False


    def ready(
        self,
    ) -> bool:

        return True


    def dump(
        self,
    ) -> dict[str, Any]:

        return {
            "name":
                "GraphValidator",

            "version":
                self.VERSION,

            "responsibility":
                self.RESPONSIBILITY,

            "ready":
                self.ready(),
        }


__all__ = [
    "GraphValidator",
]
