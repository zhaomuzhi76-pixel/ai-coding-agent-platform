from __future__ import annotations

import json

from typing import Any

from backend.agent.graph.task_graph import TaskGraph


class GraphSerializer:
    """
    TaskGraph serializer.

    Responsibility:

        - TaskGraph -> dict
        - TaskGraph -> json
        - graph storage format normalize

    Not Responsible:

        - graph validation
        - graph execution
        - graph scheduling
        - runtime restore
    """

    VERSION = "2.0"


    def to_dict(
        self,
        graph: TaskGraph,
    ) -> dict[str, Any]:

        if not isinstance(
            graph,
            TaskGraph,
        ):
            raise TypeError(
                "graph must TaskGraph"
            )

        data = graph.to_dict()

        data["serializer_version"] = (
            self.VERSION
        )

        return data


    def to_json(
        self,
        graph: TaskGraph,
    ) -> str:

        return json.dumps(
            self.to_dict(graph),
            ensure_ascii=False,
            indent=2,
        )


    def from_dict(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "data must dict"
            )

        return {
            "version": data.get(
                "version",
                "1.0",
            ),
            "nodes": data.get(
                "nodes",
                [],
            ),
        }


    def save(
        self,
        graph: TaskGraph,
        path: str,
    ) -> None:

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                self.to_json(graph)
            )


    def load(
        self,
        path: str,
    ) -> dict[str, Any]:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return self.from_dict(
                json.load(file)
            )


graph_serializer = GraphSerializer()


__all__ = [
    "GraphSerializer",
    "graph_serializer",
]
