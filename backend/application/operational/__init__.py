"""
Application operational layer package.

Subpackages are intentionally not imported eagerly.

This package must remain dependency-neutral so lower application
boundaries can import operational contracts without triggering
ProjectSession or other higher operational composition graphs.
"""

__all__ = []
