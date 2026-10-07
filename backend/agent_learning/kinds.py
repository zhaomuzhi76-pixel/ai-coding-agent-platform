"""L1 契约：偏好分类 + 作用域 + 门控阈值。"""
from __future__ import annotations
from enum import Enum


class PreferenceKind(str, Enum):
    LANGUAGE = "language"
    STYLE = "style"
    TECH_STACK = "tech_stack"
    CODE_STYLE = "code_style"
    DOMAIN = "domain"
    WORKFLOW = "workflow"
    DISLIKE = "dislike"
    OTHER = "other"


class Scope(str, Enum):
    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"


# confidence 门控（0-100）
AUTO_APPLY_THRESHOLD = 80    # ≥80 直接注入 prompt
VISIBLE_THRESHOLD = 30       # ≥30 显示在记忆面板
DEFAULT_CONFIDENCE = 60      # 新提取偏好初始置信度


# 规则提取的类别键（category.key）
RULES: tuple[tuple[str, str, str, str], ...] = (
    # (正则片段, kind, key, value 提取方式)
    (r"(?:用|回复|说|讲)\s*(中文|英文|日文)", "language", "reply_language", "grp1"),
    (r"(?:请?\s*)?(简洁|简单|详细|啰嗦|精简)(?:点|一些|点吧)?", "style", "verbosity", "grp1"),
    (r"(?:不|别|不要|避免)\s*(?:用|使用)\s*([^\s，。,.!?]{2,20})", "dislike", "avoid", "grp1"),
    (r"(?:我?喜欢|偏爱|倾向|习惯)\s*(?:用|使用)?\s*([^\s，。,.!?]{2,20})", "tech_stack", "prefer", "grp1"),
    (r"(?:缩进|indent)\s*(?:用|是|:)?\s*([24])\s*空格", "code_style", "indent", "grp1"),
    (r"(?:用|用命名)\s*(camelCase|snake_case|PascalCase)", "code_style", "naming", "grp1"),
    (r"(?:我?的?领域|专业|专注)\s*(?:是|在|:)?\s*([^\s，。,.!?]{2,20})", "domain", "domain", "grp1"),
)


__all__ = [
    "PreferenceKind", "Scope",
    "AUTO_APPLY_THRESHOLD", "VISIBLE_THRESHOLD", "DEFAULT_CONFIDENCE",
    "RULES",
]
