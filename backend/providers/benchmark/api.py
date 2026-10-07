"""模型能力测试 HTTP 端点（L3）。

职责：
    - 路由定义
    - 请求体校验
    - 组合 runner + store + report
    - 统一 {ok, data} 响应

不负责：
    - 跑测（runner 管）
    - 持久化（store 管）
    - provider 构造（resolver 管）

响应协议（对齐 /api/providers/*）：
    成功 → {"ok": true, "data": ...}
    失败 → {"ok": false, "error": {"code", "message"}}

端点：
    GET     /api/providers/benchmark/cases              列出 10 个用例
    POST    /api/providers/benchmark/run                跑一次（同步，可能 1~3 分钟）
    GET     /api/providers/benchmark/runs               历史列表
    GET     /api/providers/benchmark/runs/{run_id}      单次结果 JSON
    GET     /api/providers/benchmark/runs/{run_id}/report  纯文本报告
    GET     /api/providers/benchmark/latest             某模型最新结果
    DELETE  /api/providers/benchmark/runs/{run_id}      删除
\n\nCompat shim. See ._api_parts."""
from __future__ import annotations
from ._api_parts import *  # noqa
from ._api_parts import (BenchmarkRouter, build_benchmark_router,)  # noqa
