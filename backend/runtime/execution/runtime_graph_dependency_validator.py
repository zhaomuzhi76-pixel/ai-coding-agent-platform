from __future__ import annotations

from backend.runtime.contracts.runtime_graph import (
    RuntimeGraph,
)


class RuntimeGraphDependencyValidator:
    """
    Runtime graph dependency validator.

    Responsibility:
        - validate dependency references
        - reject self dependency

    Not Responsible:
        - cycle detection
        - topology calculation
        - execution
        - scheduling
    """

    VERSION = "1.0"

    RESPONSIBILITY = (
        "runtime_graph_dependency_validation",
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


        node_ids = graph.node_ids()


        for node in graph.all_nodes():

            for dependency in node.depends_on:

                if dependency not in node_ids:
                    raise ValueError(
                        (
                            "missing dependency: "
                            f"{dependency}"
                        )
                    )


                if dependency == node.node_id:
                    raise ValueError(
                        (
                            "self dependency: "
                            f"{node.node_id}"
                        )
                    )


        return True


    def ready(
        self,
    ) -> bool:

        return True


    def dump(
        self,
    ) -> dict[str, object]:

        return {
            "name": (
                "RuntimeGraphDependencyValidator"
            ),
            "version": self.VERSION,
            "responsibility": (
                self.RESPONSIBILITY
            ),
            "ready": self.ready(),
        }


__all__ = [
    "RuntimeGraphDependencyValidator",
]
