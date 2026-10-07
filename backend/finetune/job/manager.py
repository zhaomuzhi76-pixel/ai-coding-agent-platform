"""训练任务管理器（L1 · 单例 + 生命周期）。

职责：
    - 提交任务 → 创建 JobRecord + 落盘 + spawn asyncio task
    - 保存最新 JobRecord（内存 + store 双写）
    - 取消任务（asyncio task.cancel）
    - 事件订阅（多播到所有 listener + 落盘）

不负责：
    - 训练逻辑（runner 管）
    - 状态机（state 管）
    - 存储实现（store 管）

单例：
    get_job_manager() → 进程内唯一实例
\n\nCompat shim. See ._manager_parts."""
from __future__ import annotations
from ._manager_parts import *  # noqa
from ._manager_parts import (Any, Awaitable, Callable, JobEvent, JobManager, JobRecord, JobRunner, JobSpec, JobState, OnEvent, __all__, _manager, _store, annotations, asyncio, create_job_record, get_job_manager, is_terminal, reset_job_manager, subscribe_events, unsubscribe_events,)  # noqa
