import type {
  PersistedWorkspace,
} from "./workspace_persistence_contract"

import {
  parseWorkspace,
} from "./workspace_persistence_codec"

const LOCAL_STORAGE_KEY =
  "biancheng.ai.workspace.current"

export function writeLocalWorkspace(
  workspace: PersistedWorkspace,
): void {
  const portableWorkspace = workspace

  window.localStorage.setItem(
    LOCAL_STORAGE_KEY,
    JSON.stringify(
      portableWorkspace,
    ),
  )
}

export function readLocalWorkspace():
  PersistedWorkspace | null {
  try {
    const raw =
      window.localStorage.getItem(
        LOCAL_STORAGE_KEY,
      )

    if (!raw) {
      return null
    }

    return parseWorkspace(
      JSON.parse(raw),
    )
  } catch {
    return null
  }
}
