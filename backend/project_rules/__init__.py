"""项目管理规则持久化层。

自下而上：
    L0 rules.yaml          ← 数据真源
    L1 rule_types/schema   ← 契约
    L2 rule_loader/registry ← 加载 + 注册
    L3 rule_runner         ← 执行器
    L4 checks/*            ← 插件
    L5 scripts/*.sh        ← 命令入口
"""
from .rule_types import Rule, RuleResult, Report
from .rule_loader import load_rules
from .rule_registry import Checker, CheckerRegistry
from .rule_runner import run_all

__all__ = [
    "Rule", "RuleResult", "Report",
    "load_rules", "Checker", "CheckerRegistry", "run_all",
]
