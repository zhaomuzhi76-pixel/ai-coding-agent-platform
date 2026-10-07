"""模型能力测试结果持久化（L2）。

职责：
    - 保存 BenchmarkResult（SQLite，跨进程共享）
    - 按 provider/model 查询历史
    - 获取最新一次结果

不负责：
    - 跑测（runner 管）
    - 报告渲染（report 管）
    - HTTP（api 管）

存储：
    与 cost 共用 ~/.biancheng/metrics.db
    新表 benchmark_runs（不干扰 cost_records）
    命名具体化（save_benchmark_result 等，避免通用名）

Schema：
    benchmark_runs(
        run_id PK, provider, model,
        started_at, finished_at,
        score, rating, error,
        by_category_json, cases_json,
        case_count, passed_count
    )
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from ..evaluator import BenchmarkCaseResult
from ..runner import BenchmarkResult

_DB_DIR = Path.home() / ".biancheng"
_DB_PATH = _DB_DIR / "metrics.db"

