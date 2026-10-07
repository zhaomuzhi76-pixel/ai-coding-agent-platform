/** PendingEditSurface：批量审批面板（Claude Code 式）。
 *
 * 数据源：state.messages 里 type="step" 且 inner.type="pending_edit"。
 * 交互：勾选 + 全选 + 批量批准/拒绝。
 */
import { useMemo, useState } from "react"

import {
  useAgentWorkspaceState,
} from "../../../../app/integration/context/control_plane_context"
import {
  approveBatch,
  approveEdit,
  rejectBatch,
  rejectEdit,
  type PendingEditWire,
} from "./pending_edit_api"
import "./pending_edit_surface.css"

function extractPending(
  messages: readonly unknown[],
): PendingEditWire[] {
  const out: PendingEditWire[] = []
  const seen = new Set<string>()
  for (const m of messages) {
    if (!m || typeof m !== "object") continue
    const msg = m as Record<string, unknown>
    if (msg.type !== "step") continue
    const ev = msg.data
    if (!ev || typeof ev !== "object") continue
    const inner = ((ev as Record<string, unknown>).data ?? {}) as Record<string, unknown>
    if (inner.type !== "pending_edit") continue
    const wire = inner.pending as PendingEditWire | undefined
    if (!wire || !wire.edit_id) continue
    if (seen.has(wire.edit_id)) continue
    seen.add(wire.edit_id)
    out.push(wire)
  }
  return out
}

export function PendingEditSurface() {
  const state = useAgentWorkspaceState()
  const pending = useMemo(
    () => extractPending(state.messages as readonly unknown[]),
    [state.messages],
  )
  const [busy, setBusy] = useState(false)
  const [checked, setChecked] = useState<Set<string>>(new Set())

  // 默认全选
  useMemo(() => {
    if (pending.length === 0) return
    const ids = new Set(pending.map((p) => p.edit_id))
    setChecked(ids)
  }, [pending.length])

  if (pending.length === 0) return null

  const toggle = (id: string) => {
    const n = new Set(checked)
    n.has(id) ? n.delete(id) : n.add(id)
    setChecked(n)
  }

  const selectAll = () => setChecked(new Set(pending.map((p) => p.edit_id)))
  const clearAll = () => setChecked(new Set())

  const onApproveChecked = async () => {
    if (checked.size === 0) return
    setBusy(true)
    try {
      const ids = Array.from(checked)
      if (ids.length === 1) await approveEdit(ids[0])
      else await approveBatch(ids)
    } finally { setBusy(false) }
  }

  const onRejectChecked = async () => {
    if (checked.size === 0) return
    setBusy(true)
    try {
      const ids = Array.from(checked)
      if (ids.length === 1) await rejectEdit(ids[0])
      else await rejectBatch(ids)
    } finally { setBusy(false) }
  }

  return (
    <div className="pending-edit-surface">
      <header className="pending-edit-surface__header">
        <span>待审批 · {pending.length} 个变更</span>
        <div className="pending-edit-surface__bulk">
          <button type="button" onClick={selectAll} disabled={busy}>全选</button>
          <button type="button" onClick={clearAll} disabled={busy}>清空</button>
          <button
            type="button"
            className="pending-edit-surface__approve"
            disabled={busy || checked.size === 0}
            onClick={() => void onApproveChecked()}
          >批准选中的 {checked.size} 项</button>
          <button
            type="button"
            className="pending-edit-surface__reject"
            disabled={busy || checked.size === 0}
            onClick={() => void onRejectChecked()}
          >拒绝选中的 {checked.size} 项</button>
        </div>
      </header>

      {pending.map((p) => {
        const isChecked = checked.has(p.edit_id)
        return (
          <article
            key={p.edit_id}
            className={"pending-edit-card" + (isChecked ? " is-checked" : "")}
          >
            <div className="pending-edit-card__head">
              <label className="pending-edit-card__check">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggle(p.edit_id)}
                  disabled={busy}
                />
                <code>{p.action}</code>
              </label>
              <span className="pending-edit-card__path">{p.path}</span>
            </div>
            <pre className="pending-edit-card__diff">{p.diff}</pre>
            <div className="pending-edit-card__actions">
              <button
                type="button"
                disabled={busy}
                onClick={() => void approveEdit(p.edit_id)}
              >单独批准</button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void rejectEdit(p.edit_id)}
              >单独拒绝</button>
            </div>
          </article>
        )
      })}
    </div>
  )
}
