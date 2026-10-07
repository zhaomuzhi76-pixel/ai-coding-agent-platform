import {
  FrontendError,
} from "../contracts/errors"
import {
  decodeAgentRuntimeMessage,
  type AgentRuntimeMessage,
} from "../contracts/execution_event"
import type {
  AgentExecutionRequest,
  ExecutionResult,
} from "../contracts/execution"
import {
  clearExecution,
  connect,
  createConnection,
  rejectAll,
  stateOf,
  waitOpen,
} from "./agent_socket_connection"
import {
  toSocketPayload,
  type AgentSocketExecutionPayload,
  type AgentSocketHandlers,
  type AgentSocketState,
  type AgentSocketConnection,
} from "./agent_socket_protocol"

export type {
  AgentSocketExecutionPayload,
  AgentSocketHandlers,
  AgentSocketState,
} from "./agent_socket_protocol"

export type {
  AgentRuntimeMessage,
}

export class AgentSocket {
  private readonly connection: AgentSocketConnection
  private readonly handlers: AgentSocketHandlers
  private readonly url: string

  constructor(
    url: string,
    handlers: AgentSocketHandlers = {},
  ) {
    this.url = url
    this.handlers = handlers
    this.connection = createConnection()
  }

  connect(): void {
    connect(
      this.connection,
      this.url,
      this.handlers,
    )
  }

  async execute(
    payload: AgentSocketExecutionPayload,
  ): Promise<ExecutionResult> {
    this.validate(payload)

    // 幂等守卫 1：已有 execution 在进行中 → 直接抛错（不建连接）
    if (this.connection.execution) {
      throw new FrontendError(
        "agent websocket execution already active",
        "execution",
      )
    }

    // 幂等守卫 2：socket 处于连接中 / 已开 → 不重建（避免风暴）
    const existing = this.connection.socket
    const needNewSocket =
      !existing
      || (
        existing.readyState !== WebSocket.OPEN
        && existing.readyState !== WebSocket.CONNECTING
      )
    if (needNewSocket) {
      this.connection.socket = null
      this.connect()
    }
    await waitOpen(this.connection)

    return new Promise((resolve, reject) => {
      this.connection.execution = {
        sessionId: payload.session_id,
        resolve,
        reject,
      }

      try {
        const request =
          this.toRequest(payload)

        const socketPayload =
          toSocketPayload(request)

        this.send({
          ...socketPayload,
        })
      } catch (error) {
        clearExecution(
          this.connection,
          error,
        )
      }
    })
  }

  send(
    payload: Record<string, unknown>,
  ): void {
    const socket = this.connection.socket

    if (
      !socket
      || socket.readyState !== WebSocket.OPEN
    ) {
      throw new FrontendError(
        "agent websocket is not connected",
        "transport",
      )
    }

    socket.send(JSON.stringify(payload))
  }

  close(): void {
    rejectAll(
      this.connection,
      new FrontendError(
        "agent websocket closed",
        "transport",
      ),
    )

    this.connection.socket?.close()
    this.connection.socket = null
  }

  state(): AgentSocketState {
    return stateOf(this.connection)
  }

  toRequest(
    payload: AgentSocketExecutionPayload,
  ): AgentExecutionRequest {
    return {
      session_id: payload.session_id,
      message: payload.message,
      workspace: payload.workspace,
      domains: (payload as any).domains ?? [],
      model: {
        provider: payload.provider,
        model: payload.model,
        base_url: payload.base_url,
        api_key: payload.api_key,
      },
    }
  }

  decode(
    value: unknown,
  ): AgentRuntimeMessage {
    return decodeAgentRuntimeMessage(value)
  }

  private validate(
    payload: AgentSocketExecutionPayload,
  ): void {
    const fields = [
      "session_id",
      "message",
      "provider",
      "model",
      "workspace",
      "base_url",
      "api_key",
    ] as const

    for (const field of fields) {
      if (
        typeof payload[field] !== "string"
        || (
          field !== "api_key"
          && !payload[field].trim()
        )
      ) {
        throw new FrontendError(
          `agent ${field} required`,
          "validation",
        )
      }
    }
  }
}
