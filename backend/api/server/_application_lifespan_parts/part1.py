"""Part 1 of application_lifespan.py."""
from __future__ import annotations

import inspect

from collections.abc import Callable

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.application_lifecycle.runtime_orchestration import (
    FastAPIApplicationLifespanRuntimeOrchestrator,
)

from backend.api.application_lifecycle.runtime_orchestration import (
    FastAPIApplicationLifespanRuntimeOrchestratorFactory,
)

__all__ = [
    "ApplicationLifespan",
]
