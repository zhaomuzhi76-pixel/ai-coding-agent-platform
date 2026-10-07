import type {
  ExecutionResult,
} from "../../core/api/api_types"

import type {
  AgentWorkspaceGateway,
  AgentWorkspaceSocket,
} from "./agent_workspace_gateway"

import type {
  AgentWorkspaceState,
} from "./agent_workspace_state"

import {
  operationError,
  submissionPayload,
} from "./agent_workspace_store_support"

export interface AgentWorkspaceExecutionHandlers {
  patch(
    value: Partial<AgentWorkspaceState>,
  ): void

  appendMessage(
    message:
      AgentWorkspaceState["messages"][number],
  ): void

  setSocket(
    socket: AgentWorkspaceSocket | null,
  ): void

  isCurrent(): boolean
}

export class AgentWorkspaceExecution {
  private readonly gateway:
    AgentWorkspaceGateway

  constructor(
    gateway: AgentWorkspaceGateway,
  ) {
    this.gateway = gateway
  }

  async run(
    state: AgentWorkspaceState,
    handlers: AgentWorkspaceExecutionHandlers,
  ): Promise<ExecutionResult> {
    let request

    try {
      request =
        submissionPayload(state)
    } catch (error) {
      handlers.patch({
        phase: "error",
        error: operationError(error),
      })
      throw error
    }

    const socket =
      this.gateway.createSocket({
        onStateChange: socketState => {
          if (handlers.isCurrent()) {
            handlers.patch({
              socketState,
            })
          }
        },

        onMessage: message => {
          if (handlers.isCurrent()) {
            handlers.appendMessage(message)
          }
        },

        onError: error => {
          if (handlers.isCurrent()) {
            handlers.patch({
              phase: "error",
              error: operationError(error),
            })
          }
        },

        onResult: result => {
          if (!handlers.isCurrent()) {
            return
          }

          handlers.patch({
            phase:
              result.success === true
                ? "success"
                : "error",
            result,
            error:
              result.success === true
                ? null
                : "agent execution failed",
          })
        },
      })

    handlers.setSocket(socket)

    handlers.patch({
      phase: "executing",
      error: null,
      result: null,
    })

    try {
      return await socket.execute(request)
    } catch (error) {
      if (handlers.isCurrent()) {
        handlers.patch({
          phase: "error",
          error: operationError(error),
        })
      }

      throw error
    } finally {
      // 只在 socket 仍属于本次执行时才 close（避免互相关闭）
      try {
        socket.close()
      } catch {
        /* ignore */
      }
      if (handlers.isCurrent()) {
        handlers.setSocket(null)
      }
    }
  }
}
