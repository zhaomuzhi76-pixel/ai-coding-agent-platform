"""Part 1 of api.py."""
from __future__ import annotations

from typing import Any, Callable, Dict

from fastapi import APIRouter

from fastapi.responses import JSONResponse

from ..cases import list_cases, get_case

from ..resolver import build_runner_for

from ..store import (
    save_benchmark_result, load_benchmark_result,
    list_benchmark_runs, latest_benchmark_for,
    delete_benchmark_run,
)

from ..report import render_text

from ..compare import (
    render_compare_text, render_compare_markdown,
    build_compare_table,
)

def build_benchmark_router() -> APIRouter:
    from .main import BenchmarkRouter  # lazy
    return BenchmarkRouter().router

__all__ = ["BenchmarkRouter", "build_benchmark_router"]
