"""L4-A 交互式 ReAct 循环（对话驱动）。

Responsibility:
    - 接收一条用户消息
    - LLM 每步自主决策：调工具 → 观察 → 再决策
    - 直到 LLM 输出 done=true，返回最终回答

Not Responsible:
    - 多角色流水线（那是 L4-B edit_pipeline）
    - 后台任务编排（那是 L4-C task_loop）
    - 代码修改落盘（那是 pipeline）

调用方：agent_entry.dispatch（L3）
同层其他循环：
    - agent/orchestration/CodeEditOrchestrator  → L4-B 三角色编辑流水线
    - application/agent_orchestration/...Loop   → L4-C 后台任务编排
\n\nCompat shim. See ._agent_loop_parts."""
from __future__ import annotations
from ._agent_loop_parts import *  # noqa
from ._agent_loop_parts import (_dedup_key, run_agent_loop,)  # noqa
