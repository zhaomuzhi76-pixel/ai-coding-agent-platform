"""训练任务持久化（L1 · SQLite）。

职责：
    - jobs 表：JobRecord 增删改查
    - job_events 表：每个任务的 JobEvent 追加（append-only）
    - 与 ~/.biancheng/metrics.db 共用（不与 cost/benchmark 冲突，表名不同）

不负责：
    - 状态机（state 管）
    - 执行（runner 管）
    - 事件推送（manager 管）

命名具体化：
    save_job_record / load_job_record / list_job_records
    避免与 benchmark store 的 save_benchmark_result 混淆
\n\nCompat shim. See ._store_parts."""
from __future__ import annotations
from ._store_parts import *  # noqa
from ._store_parts import (Any, JobEvent, JobRecord, JobSpec, JobState, JobStore, Path, _DB_DIR, _DB_PATH, __all__, _ensure_schema, annotations, append_job_event, delete_job_record, json, list_job_records, load_job_events, load_job_record, reset_job_records, save_job_record, sqlite3, time, update_job_state,)  # noqa
