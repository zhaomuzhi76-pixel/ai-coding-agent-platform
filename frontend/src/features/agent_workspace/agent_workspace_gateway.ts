import { projectSessionApi } from "../../core/api/project_session_api"
import { runtimeConfig } from "../../core/config/runtime"
import type {
  SessionResponse,
  ExecutionResult,
} from "../../core/api/api_types"
import {
  AgentSocket,
  type AgentSocketExecutionPayload,
  type AgentSocketHandlers,
  type AgentSocketState,
} from "../../core/websocket/agent_socket"

export interface AgentWorkspaceSocket {
  connect(): void
  close(): void
  state(): AgentSocketState
  send(payload: Record<string, unknown>): void
  execute(
    payload: AgentSocketExecutionPayload,
  ): Promise<ExecutionResult>
}

export interface AgentWorkspaceGateway {
  loadSession(sessionId: string): Promise<SessionResponse>
  createSocket(handlers: AgentSocketHandlers): AgentWorkspaceSocket
}

export const defaultAgentWorkspaceGateway: AgentWorkspaceGateway = {
  loadSession: projectSessionApi.get,
  createSocket: handlers =>
    new AgentSocket(runtimeConfig.wsBaseUrl, handlers),
}
