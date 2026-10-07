"""审批机制单测：pending_edit / diff / gate / interceptor。

工业级契约：
  - approve → 唤醒 → 返回 approved
  - reject → 唤醒 → 返回 rejected
  - 不操作 → timeout
  - 非写操作不拦截
  - 并发多个 pending 互不干扰
\n\nCompat shim. See ._cases_approval_parts."""
from __future__ import annotations
from ._cases_approval_parts import *  # noqa
from ._cases_approval_parts import (PendingEdit, PendingGate, Suite, _gate, annotations, assert_eq, assert_in, assert_true, asyncio, diff_generator_no_change, diff_generator_produces_unified, diff_generator_truncates_large, gate_approve_flow, gate_approve_nonexistent_returns_false, gate_cleanup_removes, gate_dump_metadata, gate_list_pending, gate_reject_flow, gate_timeout_flow, gate_unknown_id, interceptor_catches_write_actions, interceptor_ignores_read_actions, make_diff, maybe_intercept, os, pending_edit_creates_unique_id, pending_edit_to_wire_shape, suite, tempfile, write_actions, write_actions_is_frozenset,)  # noqa
