"""L4 层边界测试：三套 Agent 循环职责隔离。"""
from __future__ import annotations

import inspect

from .framework import Suite, assert_true


suite = Suite("l4_boundary")


@suite.case
def l4a_react_loop_exists():
    """L4-A: agent_loop.run_agent_loop 可导入。"""
    from backend.application.agent_loop import run_agent_loop
    assert_true(callable(run_agent_loop))


@suite.case
def l4b_edit_orchestrator_exists():
    """L4-B: CodeEditOrchestrator 可导入。"""
    from backend.agent.orchestration import CodeEditOrchestrator
    assert_true(isinstance(CodeEditOrchestrator, type))


@suite.case
def l4c_task_loop_exists():
    """L4-C: AgentTaskOrchestrationLoop 可导入。"""
    from backend.application.agent_orchestration import (
        AgentTaskOrchestrationLoop,
    )
    assert_true(isinstance(AgentTaskOrchestrationLoop, type))


@suite.case
def l4a_has_boundary_doc():
    """L4-A 文件顶部声明 L4-A 标签。"""
    from backend.application.agent_loop import agent_loop as mod
    src = inspect.getsource(mod)
    assert_true("L4-A" in src, "agent_loop 缺 L4-A 边界声明")


@suite.case
def l4b_has_boundary_doc():
    """L4-B 文件顶部声明 L4-B 标签。"""
    from backend.agent.orchestration import (
        code_edit_orchestrator as mod,
    )
    src = inspect.getsource(mod)
    assert_true("L4-B" in src, "code_edit_orchestrator 缺 L4-B 声明")


@suite.case
def l4c_has_boundary_doc():
    """L4-C 文件顶部声明 L4-C 标签。"""
    from backend.application.agent_orchestration import (
        agent_task_orchestration_loop as mod,
    )
    src = inspect.getsource(mod)
    assert_true("L4-C" in src, "task_loop 缺 L4-C 声明")
