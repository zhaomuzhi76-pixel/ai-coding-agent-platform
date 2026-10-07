import type {
  FileNode,
} from "./file_tree_store"

import type {
  FileNodeSource,
} from "./file_node_source"

import {
  projectWorkspaceApi,
  type WorkspaceTreeEntry,
} from "../../../../core/api/project_workspace_api"

export function createProjectWorkspaceFileSource(
  projectId: string,
  path: string,
): FileNodeSource {
  return {
    async readText() {
      const response =
        await projectWorkspaceApi.read(
          projectId,
          path,
        )

      return response.content
    },

    async writeText(
      content: string,
    ) {
      await projectWorkspaceApi.write(
        projectId,
        path,
        content,
      )
    },
  }
}

export function createProjectWorkspaceRoot(
  projectId: string,
  name: string,
): FileNode {
  return {
    name,
    type: "directory",
    loaded: false,
    children: [],
    loadChildren: async () => {
      const response =
        await projectWorkspaceApi.list(
          projectId,
        )

      return mapEntries(
        projectId,
        response.entries,
      )
    },
  }
}

function mapEntries(
  projectId: string,
  entries: WorkspaceTreeEntry[],
): FileNode[] {
  return entries.map(
    entry => {
      if (
        entry.type === "file"
      ) {
        return {
          name: entry.name,
          type: "file" as const,
          source:
            createProjectWorkspaceFileSource(
              projectId,
              entry.path,
            ),
        }
      }

      return {
        name: entry.name,
        type: "directory" as const,
        loaded: false,
        children: [],
        loadChildren: async () => {
          const response =
            await projectWorkspaceApi.list(
              projectId,
              entry.path,
            )

          return mapEntries(
            projectId,
            response.entries,
          )
        },
      }
    },
  )
}
