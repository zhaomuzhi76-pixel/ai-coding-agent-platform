"""Main class WorkspaceFileAccess."""
from __future__ import annotations
from .mixin1 import _Mixin1
from .mixin2 import _Mixin2

class WorkspaceFileAccess(_Mixin1, _Mixin2):

    """
    Workspace file access layer.

    Responsibility:
        - resolve workspace path
        - protect path traversal
        - read file
        - write file
        - check existence

    Not Responsible:
        - lifecycle
        - scanning
        - indexing
        - analysis
    """
    VERSION = "2.1"
