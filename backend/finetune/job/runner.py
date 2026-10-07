"""训练任务执行器（L1 · asyncio 后台）。

职责：
    - 把 JobRecord + JobSpec 转成"真跑"
    - 通过 on_event 回调推送 JobEvent
    - 支持取消（asyncio.CancelledError）
    - 更新 JobRecord.state / progress / 时间戳

不负责：
    - 训练逻辑（backend 管）
    - 持久化（store 管，但调用 save/update）
    - 事件广播（manager 管）

关键设计：
    - runner 是 async 的（真跑不阻塞事件循环）
    - backend.train 若是 stub → 立即抛 NotImplementedError → state=FAILED
    - 未来真 backend 接入后，同步跑 → 用 to_thread 避免阻塞
\n\nCompat shim. See ._runner_parts."""
from __future__ import annotations
from ._runner_parts import *  # noqa
from ._runner_parts import (JobRunner, RunHandle,)  # noqa
