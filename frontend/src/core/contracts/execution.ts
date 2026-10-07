import type { ModelSelection } from "./model"

export interface AgentExecutionRequest {
  session_id: string
  message: string
  workspace: string
  model: ModelSelection
  domains?: string[]
}

export interface ExecutionResult {
  is_new_file?: boolean
  changes?: Array<{ file: string; before: string; after: string }>
  session_id?: string
  execution_id?: string
  model?: string
  output?: unknown
  success?: boolean
  error?: string
  [key: string]: unknown
}

export type ExecutionPhase =
  | "idle"
  | "connecting"
  | "running"
  | "success"
  | "error"
  | "closed"

export function validateExecutionRequest(
  request: AgentExecutionRequest,
): void {
  if (
    typeof request.session_id !== "string"
    || !request.session_id.trim()
  ) {
    throw new Error(
      "execution session id required",
    )
  }

  if (
    typeof request.message !== "string"
    || !request.message.trim()
  ) {
    throw new Error(
      "execution message required",
    )
  }

  if (
    typeof request.workspace !== "string"
    || !request.workspace.trim()
  ) {
    throw new Error(
      "execution workspace required",
    )
  }
}
