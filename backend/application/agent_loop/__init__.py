"""L4 Agent 循环：自主多步任务引擎。

对齐 Codex / Claude Code / Qwen Code 的核心循环：
    LLM 规划 → 工具调用 → 观察结果 → 再规划 → ... → 完成
"""
from .agent_loop import run_agent_loop

__all__ = ["run_agent_loop"]
