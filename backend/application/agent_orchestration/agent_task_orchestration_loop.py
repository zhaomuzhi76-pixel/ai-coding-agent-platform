"""L4-C 后台任务编排循环（目标驱动）。

Responsibility:
    - 接收 AgentRequest（目标 + 约束）
    - 每轮调 AgentTaskOrchestrator 执行一次
    - 消费 AgentDecision：terminal / 继续
    - 最多 max_iterations 轮

Not Responsible:
    - 交互式对话（L4-A）
    - 三角色编辑流水线（L4-B）

调用方：application/composition/agent_service_assembly
同层其他循环：
    - application/agent_loop/agent_loop              → L4-A ReAct
    - agent/orchestration/CodeEditOrchestrator       → L4-B 编辑流水线
\n\nCompat shim. See ._agent_task_orchestration_loop_parts."""
from __future__ import annotations
from ._agent_task_orchestration_loop_parts import *  # noqa
from ._agent_task_orchestration_loop_parts import (AgentTaskOrchestrationLoop,)  # noqa
