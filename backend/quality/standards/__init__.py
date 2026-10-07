"""工业级规则集 —— 一条命令审查 / 修复 / 测试整层。

与 backend/quality/ 现有 gate 的区别：
  - 现有 gate（layer_dependency_gate 等）：单点检查
  - 本模块：11 条规则一次性全跑，输出结构化报告
不重复职责：只读检查，不修改代码；fix 只做建议或最小改动。
"""

# ── 自动拆分避坑规则（源自 46 文件拆分实战） ──
from backend.quality.standards.auto_split_pitfalls import (  # noqa: F401
    PITFALLS,
    Pitfall,
    check_all as check_split_pitfalls,
)
