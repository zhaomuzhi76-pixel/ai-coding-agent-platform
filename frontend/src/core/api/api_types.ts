import type {
  ExecutionResult,
} from "../contracts/execution"

export interface ProjectRecord {
  project_id: string
  name: string
  root_path: string
  workspace_id: string | null
  ready: boolean
}

export interface ProjectResponse {
  name: string
  version: string
  project: ProjectRecord
  state: string
  ready: boolean
}

export interface SessionRecord {
  session_id: string
  project_id: string
  workspace_id: string | null
  runtime_id: string | null
  root_path: string
  state: string
  status: string
  metadata: Record<string, unknown>
  ready: boolean
}

export interface SessionResponse {
  name: string
  version: string
  session_id: string
  project_id: string
  workspace_id: string | null
  runtime_id: string | null
  root_path: string
  state: string
  status: string
  metadata: Record<string, unknown>
  ready: boolean
}

export interface SessionListResponse {
  project_id?: string
  sessions: SessionResponse[]
  count: number
}

export interface RemoveResponse {
  session_id: string
  removed: boolean
}

export type { ExecutionResult }
