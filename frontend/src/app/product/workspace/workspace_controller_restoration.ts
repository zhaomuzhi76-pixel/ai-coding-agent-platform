import type {
  AgentResourceBoundary,
} from "../../../core/resources/resource_boundary"

import type {
  FileNode,
} from "./explorer/file_tree_store"

import type {
  FileNodeSource,
} from "./explorer/file_node_source"
import type {
  FileTreeStore,
} from "./explorer/file_tree_store"

import type {
  WorkspaceStore,
} from "./workspace_store"

import type {
  WorkspacePersistence,
} from "./workspace_persistence_manager"

interface Dependencies {
  persistence: WorkspacePersistence
  store: WorkspaceStore
  fileTreeStore: FileTreeStore
}

interface Input {
  boundary: AgentResourceBoundary
  name: string
  root: FileNode | null
  activeFile: string | null
  activeFileSource: FileNodeSource | null
  expanded: readonly string[]
}

export async function restoreWorkspace(
  dependencies: Dependencies,
  input: Input,
): Promise<void> {
  const {
    persistence,
    store,
    fileTreeStore,
  } = dependencies

  const {
    boundary,
    name,
    root,
    activeFile,
    activeFileSource,
    expanded,
  } = input

  const restoredFile =
    activeFile ??
    (
      boundary.targetKind === "file"
        ? boundary.targetPath
        : null
    )

  persistence.beginRestore()

  persistence.setResourceKind(
    (
      boundary.targetKind === "file" &&
      name === boundary.targetPath
    )
      ? "file"
      : "directory",
  )

  try {

    const source =
      activeFileSource ?? null

    console.log(
      "RESTORE_BEFORE_STORE",
      {
        boundary,
        name,
        hasRoot: Boolean(root),
        activeFile: restoredFile,
        hasActiveSource: Boolean(source),
      },
    )

    store.setResource(
      boundary,
      name,
      restoredFile,
      source,
    )

    fileTreeStore.setFiles(
      root ? [root] : [],
    )

    fileTreeStore.setExpanded(
      expanded,
    )
  } finally {
    persistence.endRestore()
  }
}
