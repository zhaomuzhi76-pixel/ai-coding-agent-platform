"""
Workspace Runtime Package

Responsibility:

    Runtime workspace state and session objects.

Owns:

    - workspace runtime model
    - workspace runtime state

Not Responsible:

    - file access
    - repository
    - scanning
    - indexing
    - analysis
    - lifecycle management
"""


from backend.workspace.runtime.workspace_runtime import (
    WorkspaceRuntime,
)


from backend.workspace.runtime.workspace_runtime_state import (
    WorkspaceRuntimeState,
)



__all__ = [
    "WorkspaceRuntime",
    "WorkspaceRuntimeState",
]
