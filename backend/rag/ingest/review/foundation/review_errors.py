"""L1 审核门错误域。"""
from __future__ import annotations


class ReviewError(Exception):
    """审核门基类错误。"""


class StateTransitionError(ReviewError):
    """非法状态转移。"""


class DraftNotFoundError(ReviewError):
    """草稿不存在。"""


class IllegalPromotionError(ReviewError):
    """非 APPROVED 状态不得写入向量库。"""


class RecallNotAvailableError(ReviewError):
    """召回打分器不可用。"""
