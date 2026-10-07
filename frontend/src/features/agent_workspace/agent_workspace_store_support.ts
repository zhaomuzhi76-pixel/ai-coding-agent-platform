import type {
  AgentWorkspaceState,
} from "./agent_workspace_state"
import {
  validateModelSelection,
} from "../../core/contracts/model"

const DOMAINS_KEY = "biancheng.agent.domains"

function _loadDomains(): string[] {
  try {
    const raw = localStorage.getItem(DOMAINS_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

export function requireAgentSession(
  state: AgentWorkspaceState,
) {
  if (!state.session) {
    throw new Error("agent session required")
  }
  // [FOLLOW_ROLE_SENTINEL] 放行魔法值
    const _modelVal = state.model.model.trim()
    if (!_modelVal && _modelVal !== "__follow_role__") {
      throw new Error("agent model required")
    }
  if (!state.message.trim()) {
    throw new Error("agent message required")
  }
  if (state.session.status !== "active") {
    throw new Error("agent session is not active")
  }
  validateModelSelection(state.model)
  return state.session
}

export function submissionPayload(
  state: AgentWorkspaceState,
) {
  const session = requireAgentSession(state)
  // domains 优先从 localStorage 读（chips 组件已写入）；
  // state.domains 若已填充则用 state
  const stateDomains = (state as any).domains
  const domains = Array.isArray(stateDomains) && stateDomains.length > 0
    ? stateDomains
    : _loadDomains()
  const payload = {
    session_id: session.session_id,
    message: state.message.trim(),
    workspace: session.root_path,
    provider: state.model.provider,
    // [AUTO_CONVERT] "__follow_role__" → "__auto__"
      model: state.model.model.trim() === "__follow_role__"
        ? "__auto__"
        : state.model.model.trim(),
    base_url: state.model.base_url.trim(),
    api_key: state.model.api_key,
    domains,
  }
  return payload
}

export function operationError(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "agent workspace operation failed"
}

export function requireId(
  value: string,
  label: string,
): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${label} required`)
  }
  return value.trim()
}
