"""Mixin 2 of WorkspaceFileAccess."""
from __future__ import annotations
class _Mixin2:
    def dump(
        self,
    ) -> dict:

        return {
            "name":
                "WorkspaceFileAccess",

            "version":
                self.VERSION,

            "root":
                str(self.root),

            "ready":
                self.ready(),
        }
