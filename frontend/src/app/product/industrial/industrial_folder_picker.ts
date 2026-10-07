import {
  getDesktopRuntime,
} from "../../../core/desktop/desktop_runtime"

import {
  createLocalFolderRoot,
} from "../workspace/explorer/local_folder_file_source"

import {
  saveLocalRoot,
} from "../workspace/explorer/local_folder_persistence"

import type { FileNode } from "../workspace/explorer/file_tree_store"

export interface PickedFolder {
  name: string
  path: string
}

export interface PickedLocalWorkspace {
  folder: PickedFolder
  root: FileNode
}

export function desktopRuntimeAvailable(): boolean {
  return getDesktopRuntime() !== null
}

export async function pickFolder():
  Promise<PickedFolder | null> {
  const runtime = getDesktopRuntime()
  if (!runtime) {
    return null
  }
  const picked = await runtime.selectFolder()
  if (!picked) {
    return null
  }
  await saveLocalRoot(picked.path, picked.name)
  return picked
}

export async function pickLocalWorkspace():
  Promise<PickedLocalWorkspace | null> {
  const folder = await pickFolder()
  if (!folder) {
    return null
  }
  return {
    folder,
    root: createLocalFolderRoot(folder.path),
  }
}
