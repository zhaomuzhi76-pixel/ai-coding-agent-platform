import {
  request,
} from "../http/http_client"
import type {
  RemoveResponse,
  SessionListResponse,
  SessionResponse,
} from "./api_types"

export interface CreateSessionPayload {
  project_id: string
  session_id?: string
  workspace_id?: string
  runtime_id?: string
  metadata?: Record<string, unknown>
}

export interface ExecuteSessionPayload {
  session_id: string
  model: string
  [key: string]: unknown
}

export const projectSessionApi = {
  create(
    payload: CreateSessionPayload,
  ) {
    return request<SessionResponse>(
      "/project-sessions",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    )
  },

  get(sessionId: string) {
    return request<SessionResponse>(
      `/project-sessions/${encodeURIComponent(sessionId)}`,
    )
  },

  start(sessionId: string) {
    return request<SessionResponse>(
      `/project-sessions/${encodeURIComponent(sessionId)}/start`,
      { method: "POST" },
    )
  },

  close(sessionId: string) {
    return request<SessionResponse>(
      `/project-sessions/${encodeURIComponent(sessionId)}/close`,
      { method: "POST" },
    )
  },

  remove(sessionId: string) {
    return request<RemoveResponse>(
      `/project-sessions/${encodeURIComponent(sessionId)}`,
      { method: "DELETE" },
    )
  },

  active() {
    return request<SessionListResponse>(
      "/project-sessions/active",
    )
  },

  projectSessions(projectId: string) {
    return request<SessionListResponse>(
      `/projects/${encodeURIComponent(projectId)}/sessions`,
    )
  },
}
