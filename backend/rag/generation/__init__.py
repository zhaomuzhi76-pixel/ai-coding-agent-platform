"""工业级 RAG 生成层（强约束 + 拒答 + 溯源）"""
from .contracts import Citation, GroundedAnswer
from .confidence import REFUSE_THRESHOLD, calc_confidence, should_refuse
from .grounded import (
    build_grounded_context, build_prompt,
    format_answer_with_citations, make_grounded_answer,
)
from .prompt import REFUSAL_TEXT, format_context

__all__ = [
    "Citation", "GroundedAnswer",
    "REFUSE_THRESHOLD", "calc_confidence", "should_refuse",
    "build_grounded_context", "build_prompt",
    "format_answer_with_citations", "make_grounded_answer",
    "REFUSAL_TEXT", "format_context",
]
