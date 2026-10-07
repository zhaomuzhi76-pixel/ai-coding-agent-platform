import {
  FrontendError,
} from "../contracts/errors"
import type {
  ExecutionResult,
} from "../contracts/execution"
import {
  decodeAgentRuntimeMessage,
  type AgentRuntimeMessage,
} from "../contracts/execution_event"
import type {
  AgentSocketConnection,
  AgentSocketHandlers,
  AgentSocketState,
} from "./agent_socket_protocol"

export function createConnection():
  AgentSocketConnection {
  return {
    socket: null,
    openWaiters: [],
    execution: null,
  }
}

export function connect(
  connection: AgentSocketConnection,
  url: string,
  handlers: AgentSocketHandlers,
): void {
  const st = connection.socket?.readyState
  if (
    st === WebSocket.OPEN
    || st === WebSocket.CONNECTING
    || st === WebSocket.CLOSING
  ) {
    return
  }

  handlers.onStateChange?.("connecting")
  const socket = new WebSocket(url)
  connection.socket = socket

  socket.onopen = () => {
    handlers.onStateChange?.("open")

    for (
      const waiter of connection.openWaiters.splice(0)
    ) {
      waiter.resolve()
    }
  }

  socket.onmessage = event => {
    try {
      const message =
        decodeAgentRuntimeMessage(
          JSON.parse(event.data) as unknown,
        )

      handlers.onMessage?.(message)
      consume(connection, handlers, message)
    } catch (error) {
      handlers.onError?.(
        error instanceof Error
          ? error
          : new FrontendError(
              "websocket message decode failed",
              "protocol",
            ),
      )
    }
  }

  socket.onerror = () => {
    const error = new FrontendError(
      "agent websocket transport error",
      "transport",
    )
    handlers.onStateChange?.("error")
    handlers.onError?.(error)
    rejectAll(connection, error)
  }

  socket.onclose = () => {
    const error = new FrontendError(
      "agent websocket closed",
      "transport",
    )
    handlers.onStateChange?.("closed")
    connection.socket = null
    rejectAll(connection, error)
  }
}

export function waitOpen(
  connection: AgentSocketConnection,
): Promise<void> {
  if (
    connection.socket?.readyState === WebSocket.OPEN
  ) {
    return Promise.resolve()
  }

  if (
    !connection.socket
    || connection.socket.readyState === WebSocket.CLOSED
  ) {
    return Promise.reject(
      new FrontendError(
        "agent websocket connection failed",
        "transport",
      ),
    )
  }

  return new Promise((resolve, reject) => {
    connection.openWaiters.push({
      resolve,
      reject,
    })
  })
}

function consume(
  connection: AgentSocketConnection,
  handlers: AgentSocketHandlers,
  message: AgentRuntimeMessage,
): void {
  const execution = connection.execution

  if (!execution) {
    return
  }

  if (message.type === "result") {
    const result: ExecutionResult = {
      ...message.data,
      session_id: message.session_id,
      model: message.model ?? "",
    }

    handlers.onResult?.(result)
    clearExecution(
      connection,
      null,
      result,
    )
    return
  }

  if (message.type === "error") {
    clearExecution(
      connection,
      new FrontendError(
        message.data,
        "execution",
      ),
    )
  }
}

export function rejectAll(
  connection: AgentSocketConnection,
  reason: unknown,
): void {
  for (
    const waiter of connection.openWaiters.splice(0)
  ) {
    waiter.reject(reason)
  }

  clearExecution(
    connection,
    reason,
  )
}

export function clearExecution(
  connection: AgentSocketConnection,
  reason: unknown,
  result?: ExecutionResult,
): void {
  const execution = connection.execution
  connection.execution = null

  if (!execution) {
    return
  }

  if (result) {
    execution.resolve(result)
  } else {
    execution.reject(reason)
  }
}

export function stateOf(
  connection: AgentSocketConnection,
): AgentSocketState {
  if (!connection.socket) {
    return "idle"
  }

  switch (connection.socket.readyState) {
    case WebSocket.CONNECTING:
      return "connecting"
    case WebSocket.OPEN:
      return "open"
    case WebSocket.CLOSING:
    case WebSocket.CLOSED:
      return "closed"
    default:
      return "error"
  }
}
