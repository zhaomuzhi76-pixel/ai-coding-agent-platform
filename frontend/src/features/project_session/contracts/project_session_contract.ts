import type {
  ProjectResponse,
  SessionResponse,
  RemoveResponse,
} from "../../../core/api/api_types"

export type {
  ProjectResponse,
  SessionResponse,
  RemoveResponse,
}

export interface ProjectPayload {
  name: string
  root_path: string
  project_id?: string
  workspace_id?: string
}

export interface CreateSessionPayload {
  project_id: string
}
