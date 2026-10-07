"""Validate ExecutionNodeProtocol contract."""
from __future__ import annotations

from backend.core.execution import ExecutionNodeProtocol


def validate_node(node: object) -> None:
    if not isinstance(node, ExecutionNodeProtocol):
        raise TypeError("node must ExecutionNodeProtocol")
