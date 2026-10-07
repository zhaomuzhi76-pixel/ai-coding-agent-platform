"""L1 草稿状态枚举 —— 审核门的唯一真相源。"""
from __future__ import annotations

from enum import Enum


class DraftStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    WRITING = "writing"
    DONE = "done"
    REJECTED = "rejected"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in (DraftStatus.DONE, DraftStatus.REJECTED)


#: 唯一合法状态转移表
ALLOWED_TRANSITIONS: dict[DraftStatus, frozenset[DraftStatus]] = {
    DraftStatus.PENDING_REVIEW: frozenset(
        {DraftStatus.REVIEWING, DraftStatus.REJECTED}
    ),
    DraftStatus.REVIEWING: frozenset(
        {DraftStatus.APPROVED, DraftStatus.REJECTED, DraftStatus.PENDING_REVIEW}
    ),
    DraftStatus.APPROVED: frozenset({DraftStatus.WRITING, DraftStatus.REJECTED}),
    DraftStatus.WRITING: frozenset({DraftStatus.DONE, DraftStatus.FAILED}),
    DraftStatus.FAILED: frozenset({DraftStatus.WRITING}),
    DraftStatus.DONE: frozenset(),
    DraftStatus.REJECTED: frozenset(),
}
