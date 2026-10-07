/**
 * 用户模型偏好本地持久化。
 *
 * 工业级契约（对齐 Claude Code / Codex / Qwen Code）：
 *   - 记住用户上次选的模型
 *   - 跨浏览器关闭/服务器重启仍生效
 *   - 无本地记录时，前端自动选第一个可用模型
 */
import type { AgentWorkspaceState } from "../agent_workspace_state"

const KEY = "biancheng.ai.model.preference"

export type ModelSelection = AgentWorkspaceState["model"]

export function saveModelPreference(model: ModelSelection): void {
  if (!model?.model?.trim()) return
  try {
    window.localStorage.setItem(KEY, JSON.stringify(model))
  } catch {
    /* silent */
  }
}

export function loadModelPreference(): ModelSelection | null {
  try {
    const raw = window.localStorage.getItem(KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<ModelSelection>
    if (!parsed?.model || typeof parsed.model !== "string") {
      return null
    }
    return {
      provider: (parsed.provider ?? "ollama") as ModelSelection["provider"],
      model: parsed.model,
      base_url: parsed.base_url ?? "",
      api_key: parsed.api_key ?? "",
    }
  } catch {
    return null
  }
}

export function clearModelPreference(): void {
  try {
    window.localStorage.removeItem(KEY)
  } catch {
    /* silent */
  }
}
