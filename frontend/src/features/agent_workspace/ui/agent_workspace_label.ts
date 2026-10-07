/** Agent composer 的纯 label 函数（无副作用、无状态）。 */
import type { AgentWorkspaceState } from "../agent_workspace_state"

export function workspaceLabel(state: AgentWorkspaceState): string {
  return state.session?.root_path ?? "No active workspace"
}

export function toLegalProvider(
  ptype: string,
): "ollama" | "openai_compatible" {
  if (ptype === "ollama") return "ollama"
  return "openai_compatible"
}

export function modelLabel(state: AgentWorkspaceState): string {
  return (state.model.model ?? "").trim() || "Model unavailable"
}
