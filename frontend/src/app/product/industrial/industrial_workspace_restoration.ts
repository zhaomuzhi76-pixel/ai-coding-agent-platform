import type {
  PersistedWorkspace,
} from "../workspace/workspace_persistence_contract"

import {
  createProjectWorkspaceFileSource,
  createProjectWorkspaceRoot,
} from "../workspace/explorer/project_workspace_file_source"

import type {
  WorkspaceController,
} from "../workspace/workspace_controller"



function normalizePath(
  value: string,
): string {
  return value
    .replace(/\\/g, "/")
    .replace(/^\/+|\/+$/g, "")
}

function relativeResourcePath(
  value: string,
  root: string,
): string {
  const filePath =
    normalizePath(value)

  const rootPath =
    normalizePath(root)

  if (
    rootPath &&
    filePath.startsWith(
      `${rootPath}/`,
    )
  ) {
    return filePath.slice(
      rootPath.length + 1,
    )
  }

  return filePath
}

export async function restoreIndustrialWorkspace(
  persisted: PersistedWorkspace,
  controller: WorkspaceController,
): Promise<void> {
  const started =
    performance.now()

  const projectId =
    persisted.boundary.projectId

  if (
    !projectId ||
    persisted.kind !== "directory"
  ) {
    console.warn(
      "WORKSPACE_RESTORE_PROJECT_UNAVAILABLE",
      {
        name: persisted.name,
        projectId,
      },
    )
    return
  }

  const root =
    createProjectWorkspaceRoot(
      projectId,
      persisted.name,
    )

  const files = [root]

  const activeFileSource =
    persisted.activeFile
      ? createProjectWorkspaceFileSource(
          projectId,
          relativeResourcePath(
            persisted.activeFile,
            persisted.name,
          ),
        )
      : null

  console.log(
    "RESTORE_BEFORE_CONTROLLER",
    Math.round(
      performance.now() - started,
    ),
  )

  await controller.restore(
    persisted.boundary,
    persisted.name,
    files[0] ?? null,
    persisted.activeFile,
    persisted.expanded.length > 0
      ? persisted.expanded
      : [
          persisted.name,
        ],
    activeFileSource,
  )

  console.log(
    "RESTORE_TOTAL_TIME",
    Math.round(
      performance.now() - started,
    ),
  )
}

