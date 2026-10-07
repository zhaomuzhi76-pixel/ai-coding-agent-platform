import {
  projectApi,
} from "../../core/api/project_api"
import {
  projectSessionApi,
  type CreateSessionPayload,
} from "../../core/api/project_session_api"
import type {
  ProjectResponse,
  RemoveResponse,
  SessionListResponse,
  SessionResponse,
} from "../../core/api/api_types"

export interface ProjectSessionFeatureGateway {
  getProject(
    projectId: string,
  ): Promise<ProjectResponse>
  createProject(
    payload: {
      name: string
      root_path: string
      project_id?: string
      workspace_id?: string
    },
  ): Promise<ProjectResponse>
  removeProject(
    projectId: string,
  ): Promise<ProjectResponse>
  createSession(
    payload: CreateSessionPayload,
  ): Promise<SessionResponse>
  loadSession(
    sessionId: string,
  ): Promise<SessionResponse>
  startSession(
    sessionId: string,
  ): Promise<SessionResponse>
  closeSession(
    sessionId: string,
  ): Promise<SessionResponse>
  removeSession(
    sessionId: string,
  ): Promise<RemoveResponse>
  projectSessions(
    projectId: string,
  ): Promise<SessionListResponse>
}

export const defaultProjectSessionGateway:
  ProjectSessionFeatureGateway = {
    getProject: projectApi.get,
    createProject: projectApi.create,
    removeProject: projectApi.remove,
    createSession: projectSessionApi.create,
    loadSession: projectSessionApi.get,
    startSession: projectSessionApi.start,
    closeSession: projectSessionApi.close,
    removeSession: projectSessionApi.remove,
    projectSessions:
      projectSessionApi.projectSessions,
  }
