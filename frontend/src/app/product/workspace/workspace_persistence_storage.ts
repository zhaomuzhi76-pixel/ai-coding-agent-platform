import type {
  PersistedWorkspace,
} from "./workspace_persistence_contract"

import {  parseWorkspace,
} from "./workspace_persistence_codec"

import {
  readLocalWorkspace,
  writeLocalWorkspace,
} from "./workspace_persistence_local_storage"

import {
  readIndexedWorkspace,
  writeIndexedWorkspace,
} from "./workspace_persistence_indexeddb"

import {
  IncrementalWorkspaceStore,
} from "./workspace_persist_incremental"

// ═══ 增量模式开关（默认关闭，零破坏升级）═══
// 开启方式（任一）：
//   1. 浏览器 window.__LOCO_PERSIST_INCREMENTAL__ = true
//   2. Vite env: VITE_PERSIST_INCREMENTAL=1
function _readIncrementalFlag(): boolean {
  if (typeof window !== "undefined") {
    const w = window as unknown as { __LOCO_PERSIST_INCREMENTAL__?: unknown }
    if (w.__LOCO_PERSIST_INCREMENTAL__ === true) return true
  }
  try {
    const env = (import.meta as unknown as { env?: Record<string, string> }).env
    if (env && env.VITE_PERSIST_INCREMENTAL === "1") return true
  } catch { /* ignore */ }
  return false
}

const USE_INCREMENTAL = _readIncrementalFlag()
const incrementalStore = new IncrementalWorkspaceStore()


export async function saveWorkspace(
  workspace: PersistedWorkspace,
): Promise<void> {
  // 主存储：IndexedDB（异步，不动）
  await writeIndexedWorkspace(
    workspace,
  )

  // 备份：localStorage（同步）
  try {
    if (USE_INCREMENTAL) {
      // 增量写（首次全量 + 后续 patch）
      incrementalStore.save(workspace)
      // 兼容层：仍全量写 legacy key（供未升级的读方）
      writeLocalWorkspace(workspace)
    } else {
      // 现状：全量写
      writeLocalWorkspace(workspace)
    }
  } catch {
    // localStorage is metadata-only and optional.
  }
}

export async function loadWorkspace():
  Promise<PersistedWorkspace | null> {
  try {
    const indexed =
      await readIndexedWorkspace()

    if (indexed) {
      return indexed
    }
  } catch {
    // Fall through to metadata fallback.
  }

  // 回退：优先增量 store，失败再 legacy
  if (USE_INCREMENTAL) {
    try {
      const inc = incrementalStore.load()
      if (inc) return inc
    } catch { /* fall through */ }
  }

  return readLocalWorkspace()
}

export {  parseWorkspace,
}

// ═══ 可选诊断/管理 API（供后续接入）═══
export function incrementalPersistenceStats() {
  return {
    enabled: USE_INCREMENTAL,
    stats: incrementalStore.stats(),
  }
}

export function compactIncrementalPersistence() {
  if (!USE_INCREMENTAL) return
  const current = incrementalStore.load()
  if (current) incrementalStore.compact(current)
}

export function clearIncrementalPersistence() {
  incrementalStore.clear()
}
