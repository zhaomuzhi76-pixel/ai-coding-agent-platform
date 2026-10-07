/** Agent 审批 HTTP 客户端。 */
import { runtimeConfig } from "../../../../core/config/runtime"

export interface PendingEditWire {
  edit_id: string
  action: string
  path: string
  diff: string
  created_at: number
  has_old: boolean
  has_new: boolean
}

async function post(path: string): Promise<boolean> {
  try {
    const r = await fetch(`${runtimeConfig.apiBaseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
    const j = await r.json()
    return Boolean(j?.ok)
  } catch {
    return false
  }
}

export function approveEdit(editId: string): Promise<boolean> {
  return post(`/agent/approve/${encodeURIComponent(editId)}`)
}

export function rejectEdit(editId: string): Promise<boolean> {
  return post(`/agent/reject/${encodeURIComponent(editId)}`)
}


export async function approveBatch(editIds: string[]): Promise<boolean> {
  if (editIds.length === 0) return true
  try {
    const r = await fetch(`${runtimeConfig.apiBaseUrl}/agent/approve-batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edit_ids: editIds }),
    })
    const j = await r.json()
    return Boolean(j?.ok)
  } catch {
    return false
  }
}

export async function rejectBatch(editIds: string[]): Promise<boolean> {
  if (editIds.length === 0) return true
  try {
    const r = await fetch(`${runtimeConfig.apiBaseUrl}/agent/reject-batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ edit_ids: editIds }),
    })
    const j = await r.json()
    return Boolean(j?.ok)
  } catch {
    return false
  }
}
