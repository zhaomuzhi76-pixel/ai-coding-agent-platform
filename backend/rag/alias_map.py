"""中药材别名映射（单一职责）。

职责：
  - 常见别名 → CHM-100 标准名（如 黄耆 → 黄芪）
  - 查询时先归一别名，再检索

不做：
  - 不检索、不改写（各自模块管）
"""
from __future__ import annotations
from typing import Optional

# 常见别名 → 标准名
_ALIAS = {
    # 黄芪类
    # 玄参类
    "黑参": "玄参",
    # 金银花类
    "银花": "金银花",
    "二花": "金银花",
    "双花": "金银花",
    # 甘草类
    "国老": "甘草",
    "美草": "甘草",
    # 人参类
    "神草": "人参",
    # 地黄类
    "生地": "地黄",
    "熟地": "地黄",
    # 天麻类
    "赤箭": "天麻",
    # 川芎类
    "芎劳": "川芎",
    # 白芍/赤芍
    "芍药": "白芍",
    # 荷叶类
    "莲叶": "荷叶",
    # 乌梅类
    "酸梅": "乌梅",
    # 生姜
    "姜": "生姜",
    # [BIAN] 异体字/繁简/简繁
    "苏子": "紫苏子",
    "苏叶": "紫苏叶",
    "苏梗": "紫苏梗",
    "黑丑": "牵牛子",
    "白丑": "牵牛子",
}


def normalize_alias(query: str) -> str:
    """把 query 里的别名替换成标准名。失败返回原 query。"""
    q = (query or "").strip()
    if not q:
        return q
    out = q
    for alias, std in _ALIAS.items():
        if alias in out:
            out = out.replace(alias, std)
    return out


def lookup_alias(name: str) -> Optional[str]:
    """单名归一。"""
    return _ALIAS.get((name or "").strip())


__all__ = ["normalize_alias", "lookup_alias", "_ALIAS"]
