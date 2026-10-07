"""
============================================================
BianCheng AI Agent Pro
Enterprise AI Agent Platform
============================================================

Author  : ZhaoMuZhi & OpenAI
License : MIT
Python  : 3.10+
"""

from __future__ import annotations

from pathlib import Path

# ----------------------------------------------------------------------
# Project Metadata
# ----------------------------------------------------------------------

APP_NAME: str = "BianCheng AI Agent Pro"

APP_DESCRIPTION: str = (
    "Enterprise AI Agent Platform for Coding, Office Automation "
    "and Multi-Agent Workflow."
)

__version__: str = "0.1.0"

__author__: str = "ZhaoMuZhi"

__license__: str = "MIT"

# ----------------------------------------------------------------------
# Project Paths
# ----------------------------------------------------------------------

BACKEND_DIR: Path = Path(__file__).resolve().parent

PROJECT_ROOT: Path = BACKEND_DIR.parent

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

__all__ = [
    "APP_NAME",
    "APP_DESCRIPTION",
    "__version__",
    "__author__",
    "__license__",
    "PROJECT_ROOT",
    "BACKEND_DIR",
]

# ----------------------------------------------------------------------
# Self Test
# ----------------------------------------------------------------------
