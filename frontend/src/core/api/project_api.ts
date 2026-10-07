import {
  request,
} from "../http/http_client"
import type {
  ProjectResponse,
} from "./api_types"

export interface CreateProjectPayload {
  name: string
  root_path: string
  project_id?: string
  workspace_id?: string
}

export const projectApi = {
  create(
    payload: CreateProjectPayload,
  ) {
    return request<ProjectResponse>(
      "/projects",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    )
  },

  get(projectId: string) {
    return request<ProjectResponse>(
      `/projects/${encodeURIComponent(projectId)}`,
    )
  },

  remove(projectId: string) {
    return request<ProjectResponse>(
      `/projects/${encodeURIComponent(projectId)}`,
      {
        method: "DELETE",
      },
    )
  },
}
