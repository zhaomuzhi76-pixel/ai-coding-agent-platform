import type {
  AgentExecutionRequest,
  ExecutionResult,
} from "../contracts/execution"
import type {
  AgentRuntimeMessage,
} from "../contracts/execution_event"
import type {
  ModelSelection,
} from "../contracts/model"

export type AgentSocketState =
  | "idle"
  | "connecting"
  | "open"
  | "closed"
  | "error"

export interface AgentSocketExecutionPayload {
  session_id: string
  message: string
  provider: ModelSelection["provider"]
  model: string
  workspace: string
  base_url: string
  api_key: string
  domains?: string[]
}

export interface AgentSocketHandlers {
  onStateChange?: (
    state: AgentSocketState,
  ) => void
  onMessage?: (
    message: AgentRuntimeMessage,
  ) => void
  onError?: (
    error: Error,
  ) => void
  onResult?: (
    result: ExecutionResult,
  ) => void
}

export interface AgentSocketConnection {
  socket: WebSocket | null
  openWaiters: Array<{
    resolve: () => void
    reject: (reason?: unknown) => void
  }>
  execution: {
    sessionId: string
    resolve: (value: ExecutionResult) => void
    reject: (reason?: unknown) => void
  } | null
}

export function toSocketPayload(
  request: AgentExecutionRequest,
): AgentSocketExecutionPayload {
  return {
    session_id: request.session_id,
    message: request.message,
    provider: request.model.provider,
    model: request.model.model,
    workspace: request.workspace,
    base_url: request.model.base_url,
    api_key: request.model.api_key,
    domains: request.domains ?? [],
  }
}
