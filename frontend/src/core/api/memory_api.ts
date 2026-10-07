/** Agent 学习 / 用户偏好 API（含作用域）。 */
import { request } from "../http/http_client"

export type RuleScope = "global" | "project" | "session"

export interface Preference {
  id: number
  kind: string
  key: string
  value: string
  confidence: number
  sample_count: number
  auto_applied: boolean
  scope: RuleScope
  workspace: string
  last_used_at: number
  created_at: number
}

export const SCOPE_LABEL: Record<RuleScope, string> = {
  global: "全局", project: "项目", session: "会话",
}

export const memoryApi = {
  list: (minConfidence = 0, scope = "", workspace = "") =>
    request<{ preferences: Preference[] }>(
      `/memory/preferences?min_confidence=${minConfidence}` +
      `&scope=${encodeURIComponent(scope)}` +
      `&workspace=${encodeURIComponent(workspace)}`),

  add: (p: {
    kind: string; key: string; value: string
    confidence?: number; scope?: RuleScope; workspace?: string
  }) =>
    request<{ id: number; created?: boolean; updated?: boolean }>(
      "/memory/preferences",
      { method: "POST", body: JSON.stringify(p) }),

  remove: (id: number) =>
    request<{ deleted: boolean }>(`/memory/preferences/${id}`,
      { method: "DELETE" }),

  setConfidence: (id: number, confidence: number) =>
    request<{ updated: boolean }>(
      `/memory/preferences/${id}/confidence`,
      { method: "POST", body: JSON.stringify({ confidence }) }),

  setScope: (id: number, scope: RuleScope, workspace = "") =>
    request<{ updated: boolean }>(
      `/memory/preferences/${id}/scope`,
      { method: "POST", body: JSON.stringify({ scope, workspace }) }),

  extract: (text: string, useLlm = false) =>
    request<{ candidates: unknown[]; stored: number }>(
      "/memory/extract",
      { method: "POST", body: JSON.stringify({ text, use_llm: useLlm }) }),

  context: (autoOnly = true) =>
    request<{ context: string }>(`/memory/context?auto_only=${autoOnly}`),

  stats: () =>
    request<{ total: number; auto_applied: number; visible: number }>(
      "/memory/stats"),
}
