import {
  request,
} from "../http/http_client"

export interface WorkspaceTreeEntry {
  name: string
  type: "file" | "directory"
  path: string
}

export interface WorkspaceTreeResponse {
  project_id: string
  path: string
  entries: WorkspaceTreeEntry[]
  count: number
}

export interface WorkspaceFileResponse {
  project_id: string
  path: string
  content: string
}

export interface WorkspaceWriteResponse {
  project_id: string
  path: string
  written: boolean
}

export const projectWorkspaceApi = {
  list(
    projectId: string,
    path = "",
  ) {
    const query =
      path
        ? `?path=${encodeURIComponent(path)}`
        : ""

    return request<WorkspaceTreeResponse>(
      `/projects/${encodeURIComponent(projectId)}/workspace/tree${query}`,
    )
  },

  read(
    projectId: string,
    path: string,
  ) {
    return request<WorkspaceFileResponse>(
      `/projects/${encodeURIComponent(projectId)}/workspace/file?path=${encodeURIComponent(path)}`,
    )
  },

  write(
    projectId: string,
    path: string,
    content: string,
  ) {
    return request<WorkspaceWriteResponse>(
      `/projects/${encodeURIComponent(projectId)}/workspace/file`,
      {
        method: "PUT",
        body: JSON.stringify({
          path,
          content,
        }),
      },
    )
  },
}
