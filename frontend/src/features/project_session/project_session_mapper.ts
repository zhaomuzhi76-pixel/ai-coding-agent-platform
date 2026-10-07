
import type {
  ProjectResponse,
  SessionResponse,
} from "../../core/api/api_types"

export interface ProjectSessionProjectView {
  projectId: string
  name: string
  rootPath: string
  workspaceId: string | null
}

export interface ProjectSessionInfoView {
  id: string
  projectId: string
  workspaceId: string | null
  rootPath: string
  status: string
  ready: boolean
}

export function mapProject(
  value: ProjectResponse,
): ProjectSessionProjectView {
  return {
    projectId: value.project.project_id,
    name: value.project.name,
    rootPath: value.project.root_path,
    workspaceId: value.project.workspace_id,
  }
}

export function mapSession(
  value: SessionResponse,
): ProjectSessionInfoView {
  return {
    id: value.session_id,
    projectId: value.project_id,
    workspaceId: value.workspace_id,
    rootPath: value.root_path,
    status: value.status,
    ready: value.ready,
  }
}
