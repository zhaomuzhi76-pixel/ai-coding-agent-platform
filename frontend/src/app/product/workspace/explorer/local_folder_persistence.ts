import {
  allowRoot,
} from "../../../../core/desktop/desktop_runtime"

import {
  persistGet,
  persistSet,
} from "../../../../core/desktop/desktop_persist_service"

import {
  createLocalFolderRoot,
} from "./local_folder_file_source"

import type { FileNode } from "./file_tree_store"

const KEY_V2 = "workspace.local.root.v2"
const KEY_V1 = "workspace.local.root.v1"

export interface PersistedLocalRoot {
  path: string
  name: string
  expanded: string[]
}

async function migrateV1(): Promise<void> {
  const legacy = (await persistGet(KEY_V1)) as
    | { path?: string; name?: string }
    | null

  if (
    !legacy ||
    typeof legacy.path !== "string" ||
    typeof legacy.name !== "string"
  ) {
    return
  }

  const existing = (await persistGet(KEY_V2)) as
    | PersistedLocalRoot
    | null

  if (existing && typeof existing.path === "string") {
    return
  }

  await persistSet(KEY_V2, {
    path: legacy.path,
    name: legacy.name,
    expanded: [],
  })
}

export async function saveLocalRoot(
  path: string,
  name: string,
): Promise<void> {
  const prev = await loadLocalRoot()
  await persistSet(KEY_V2, {
    path,
    name,
    expanded:
      prev && prev.path === path
        ? prev.expanded
        : [],
  })
}

export async function saveExpanded(
  expanded: readonly string[],
): Promise<void> {
  const prev = await loadLocalRoot()
  if (!prev) {
    return
  }
  await persistSet(KEY_V2, {
    ...prev,
    expanded: [...expanded],
  })
}

export async function loadLocalRoot():
  Promise<PersistedLocalRoot | null> {
  await migrateV1()

  const data = (await persistGet(KEY_V2)) as
    | PersistedLocalRoot
    | null

  if (!data || typeof data.path !== "string") {
    return null
  }

  await allowRoot(data.path)

  return {
    path: data.path,
    name:
      typeof data.name === "string"
        ? data.name
        : data.path.split("/").filter(Boolean).pop() ?? data.path,
    expanded: Array.isArray(data.expanded)
      ? data.expanded.filter(
          item => typeof item === "string",
        )
      : [],
  }
}

export async function buildRestoredLocalRoot():
  Promise<{
    root: FileNode
    path: string
    name: string
    expanded: string[]
  } | null> {
  const data = await loadLocalRoot()
  if (!data) {
    return null
  }
  return {
    root: createLocalFolderRoot(data.path),
    path: data.path,
    name: data.name,
    expanded: data.expanded,
  }
}
