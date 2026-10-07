"""内置触发规则。保守策略：只匹配"高置信度"模式，宁可漏触发不误触发。
用户可扩：新建自己的 rules 文件 + TriggerMatcher([...]) 传入。
每条规则对应一个工具；arg_map 用正则组号映射到工具参数。"""
from __future__ import annotations
from backend.agent_tools.trigger.contracts import TriggerRule

BUILTIN_RULES: tuple = (
    # ─── 文件系统（fs.* MCP）───
    TriggerRule(
        id="fs.list_directory",
        pattern=r"列出\s+(/[^\s，,。;；]+|[\w./-]{2,})\s*(下|目录)?(的)?(文件|目录|内容)?",
        tool="fs.list_directory",
        arg_map={"path": 1},
        priority=10,
    ),
    TriggerRule(
        id="fs.read_text_file",
        pattern=r"(读|打开|查看|看看|读取).{0,6}?(/[^\s，,。;；]+\.(?:txt|md|py|json|log|yaml|yml|toml|ini|conf|csv))",
        tool="fs.read_text_file",
        arg_map={"path": 2},
        priority=10,
    ),
    TriggerRule(
        id="fs.directory_tree",
        pattern=r"(目录树|树形展示|tree)\s*(/[^\s，,。;；]+)?",
        tool="fs.directory_tree",
        arg_map={"path": 2},
        priority=12,
    ),

    # ─── 中医 ───
    TriggerRule(
        id="tcm.term",
        pattern=r"(气虚|血瘀|阴阳|五行|经络|气滞|痰湿|肝火|肾虚|脾虚|气血两虚|肝阳上亢|风寒|风热)",
        tool="domain.lookup.tcm",
        arg_map={"term": 1},
        priority=20,
    ),

    # ─── 农业 ───
    TriggerRule(
        id="agri.crop",
        pattern=r"(小麦|玉米|水稻|大豆|棉花|花生|马铃薯|甘薯|高粱|谷子)",
        tool="domain.lookup.agriculture",
        arg_map={"term": 1},
        priority=20,
    ),

    # ─── 金融 ───
    TriggerRule(
        id="fin.term",
        pattern=r"(股票|基金|保险|债券|期货|期权|利率|汇率|IPO|ETF)",
        tool="domain.lookup.finance",
        arg_map={"term": 1},
        priority=20,
    ),

    # ─── RAG 领域强触发（含领域关键词且问"是什么/详情/介绍"）───
    TriggerRule(
        id="rag.tcm.explain",
        pattern=r"(中医|中药|方剂).{0,8}(是什么|有哪些|详情|介绍|解释)",
        tool="rag.search_tcm",
        arg_map={"query": 0},
        priority=30,
    ),
    TriggerRule(
        id="rag.agri.explain",
        pattern=r"(农业|作物|种植).{0,8}(是什么|怎么|防治|详情)",
        tool="rag.search_agriculture",
        arg_map={"query": 0},
        priority=30,
    ),
    TriggerRule(
        id="rag.finance.explain",
        pattern=r"(金融|投资|理财).{0,8}(是什么|怎么|详情)",
        tool="rag.search_finance",
        arg_map={"query": 0},
        priority=30,
    ),
)

__all__ = ["BUILTIN_RULES"]
