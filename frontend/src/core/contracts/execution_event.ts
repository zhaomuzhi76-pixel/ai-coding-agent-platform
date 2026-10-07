export type RuntimeEventType =
  | "node_start"
  | "node_finish"
  | "node_failed"
  | "tool_call"
  | "pending_edit"
  | "tool_result"

export interface RuntimeEventV2 {
  schema: "runtime.event.v2"
  event_id: string
  type: RuntimeEventType
  node_id?: string
  data: Record<string, unknown>
  metadata: Record<string, unknown>
  source: string
  timestamp: string
  version: string
  responsibility: string[]
}

export interface RuntimeStepMessage {
  type: "step"
  session_id: string
  data: RuntimeEventV2
}

export interface RuntimeResultMessage {
  type: "result"
  session_id: string
  model?: string
  data: Record<string, unknown>
}

export interface RuntimeEndMessage {
  type: "end"
  session_id: string
  model?: string
}

export interface RuntimeErrorMessage {
  type: "error"
  session_id: string
  data: string
}

export interface RuntimeTokenMessage {
  type: "token"
  session_id: string
  content: string
}

export type AgentRuntimeMessage =
  | RuntimeStepMessage
  | RuntimeResultMessage
  | RuntimeEndMessage
  | RuntimeErrorMessage
  | RuntimeTokenMessage

export function isRuntimeEventV2(
  value: unknown,
): value is RuntimeEventV2 {
  if (
    typeof value !== "object"
    || value === null
  ) {
    return false
  }

  const event = value as Record<string, unknown>

  return (
    event.schema === "runtime.event.v2"
    && typeof event.event_id === "string"
    && typeof event.type === "string"
    && typeof event.data === "object"
    && event.data !== null
    && typeof event.metadata === "object"
    && event.metadata !== null
    && typeof event.source === "string"
    && typeof event.timestamp === "string"
    && typeof event.version === "string"
    && Array.isArray(event.responsibility)
  )
}

export function decodeAgentRuntimeMessage(
  value: unknown,
): AgentRuntimeMessage {
  if (
    typeof value !== "object"
    || value === null
  ) {
    throw new Error(
      "invalid websocket message",
    )
  }

  const message = value as Record<string, unknown>

  if (
    typeof message.session_id !== "string"
    || !message.session_id.trim()
  ) {
    throw new Error(
      "websocket session id required",
    )
  }

  // 协议层心跳（uvicorn 或应用层）：无 session_id，直接跳过
  if (message.type === "ping" || message.type === "pong") {
    return { type: "end" as const, session_id: "__heartbeat__", model: undefined }
  }

  const sessionId = message.session_id

  if (message.type === "step") {
    if (!isRuntimeEventV2(message.data)) {
      throw new Error(
        "invalid runtime.event.v2 payload",
      )
    }

    return {
      type: "step",
      session_id: sessionId,
      data: message.data,
    }
  }

  if (message.type === "result") {
    if (
      typeof message.data !== "object"
      || message.data === null
    ) {
      throw new Error(
        "invalid execution result payload",
      )
    }

    return {
      type: "result",
      session_id: sessionId,
      model:
        typeof message.model === "string"
          ? message.model
          : undefined,
      data:
        message.data as Record<string, unknown>,
    }
  }

  if (message.type === "end") {
    return {
      type: "end",
      session_id: sessionId,
      model:
        typeof message.model === "string"
          ? message.model
          : undefined,
    }
  }

  if (message.type === "token") {
    if (
      typeof message.data !== "string"
    ) {
      throw new Error(
        "invalid token payload",
      )
    }

    return {
      type: "token",
      session_id: sessionId,
      content: message.data,
    }
  }

  if (message.type === "error") {
    return {
      type: "error",
      session_id: sessionId,
      data:
        typeof message.data === "string"
          ? message.data
          : "agent execution failed",
    }
  }

  throw new Error(
    "unsupported websocket message type",
  )
}
