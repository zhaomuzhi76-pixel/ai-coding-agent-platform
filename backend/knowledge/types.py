from __future__ import annotations

from enum import Enum
from typing import Dict


class KnowledgeType(
    str,
    Enum,
):
    """
    Persistent knowledge categories.
    """

    USER_PREFERENCE = "USER_PREFERENCE"

    USER_RULE = "USER_RULE"

    CODING_STYLE = "CODING_STYLE"

    WORKFLOW_RULE = "WORKFLOW_RULE"

    PROJECT_RULE = "PROJECT_RULE"

    ARCHITECTURE_DECISION = "ARCHITECTURE_DECISION"

    SYSTEM_FACT = "SYSTEM_FACT"

    ERROR_SOLUTION = "ERROR_SOLUTION"

    TASK_HISTORY = "TASK_HISTORY"



DEFAULT_IMPORTANCE: Dict[str, int] = {

    KnowledgeType.USER_RULE:
        10,

    KnowledgeType.PROJECT_RULE:
        10,

    KnowledgeType.ARCHITECTURE_DECISION:
        9,

    KnowledgeType.CODING_STYLE:
        8,

    KnowledgeType.WORKFLOW_RULE:
        8,

    KnowledgeType.ERROR_SOLUTION:
        7,

    KnowledgeType.USER_PREFERENCE:
        7,

    KnowledgeType.SYSTEM_FACT:
        6,

    KnowledgeType.TASK_HISTORY:
        5,

}



def get_default_importance(
    knowledge_type: str,
) -> int:
    """
    Get default knowledge importance.
    """

    return DEFAULT_IMPORTANCE.get(
        knowledge_type,
        5,
    )



def is_long_term(
    knowledge_type: str,
) -> bool:
    """
    Whether knowledge should persist permanently.
    """

    return knowledge_type in {

        KnowledgeType.USER_RULE,

        KnowledgeType.PROJECT_RULE,

        KnowledgeType.ARCHITECTURE_DECISION,

        KnowledgeType.CODING_STYLE,

        KnowledgeType.WORKFLOW_RULE,

    }



__all__ = [
    "KnowledgeType",
    "DEFAULT_IMPORTANCE",
    "get_default_importance",
    "is_long_term",
]
