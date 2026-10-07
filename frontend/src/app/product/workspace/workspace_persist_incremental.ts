/**
 * 增量版 localStorage 持久化（兼容老全量格式）。
 *
 * 存储 key：
 *   base    = "biancheng.ai.workspace.base"     首次全量
 *   patches = "biancheng.ai.workspace.patches"  后续增量
 *   mode    = "biancheng.ai.workspace.mode"     标记模式
 *   legacy  = "biancheng.ai.workspace.current"  兼容旧版（同步写）
 *
 * 契约：
 *   - load()：优先增量模式，失败回退 legacy
 *   - save()：首次全量；后续 patch；patch 数/字节超阈值 → 压缩
 *   - compact()：手动把最新状态变新 base
 *   - clear()：清所有 key
 *   - stats()：诊断
 *
 * 不负责：
 *   - IndexedDB（异步全量由 storage 层管）
 *   - diff/apply 算法（patch 层管）
 */
import type { PersistedWorkspace } from "./workspace_persistence_contract"
import {
  applyWorkspace,
  deserializePatches,
  diffWorkspace,
  serializePatches,
  type PatchOp,
} from "./workspace_persist_patch"

const BASE_KEY = "biancheng.ai.workspace.base"
const PATCHES_KEY = "biancheng.ai.workspace.patches"
const MODE_KEY = "biancheng.ai.workspace.mode"
const LEGACY_KEY = "biancheng.ai.workspace.current"

const MODE_INCREMENTAL = "incremental"

const DEFAULT_MAX_PATCHES = 200
const DEFAULT_MAX_BYTES = 100 * 1024

export interface IncrementalStats {
  mode: "incremental" | "full" | "empty"
  baseBytes: number
  patchesCount: number
  patchesBytes: number
  totalBytes: number
}

function safeGet(key: string): string | null {
  try { return window.localStorage.getItem(key) } catch { return null }
}

function safeSet(key: string, value: string): void {
  try { window.localStorage.setItem(key, value) } catch { /* quota */ }
}

function safeRemove(key: string): void {
  try { window.localStorage.removeItem(key) } catch { /* noop */ }
}

export class IncrementalWorkspaceStore {
  VERSION = "1.0"
  private readonly maxPatches: number
  private readonly maxBytes: number
  private readonly writeLegacy: boolean

  constructor(opts?: { maxPatches?: number; maxBytes?: number; writeLegacy?: boolean }) {
    this.maxPatches = opts?.maxPatches ?? DEFAULT_MAX_PATCHES
    this.maxBytes = opts?.maxBytes ?? DEFAULT_MAX_BYTES
    this.writeLegacy = opts?.writeLegacy ?? true
  }

  load(): PersistedWorkspace | null {
    const mode = safeGet(MODE_KEY)
    if (mode === MODE_INCREMENTAL) {
      const base = this._readBase()
      if (base) {
        const patches = this._readPatches()
        try {
          return applyWorkspace(base, patches)
        } catch {
          // 应用失败 → 回退 legacy
        }
      }
    }
    return this._readLegacy()
  }

  save(workspace: PersistedWorkspace): void {
    const base = this._readBase()
    if (base === null) {
      this._writeBase(workspace)
      this._writePatches([])
      safeSet(MODE_KEY, MODE_INCREMENTAL)
      if (this.writeLegacy) this._writeLegacy(workspace)
      return
    }

    const patches = this._readPatches()
    let lastState: PersistedWorkspace
    try {
      lastState = applyWorkspace(base, patches)
    } catch {
      // 状态损坏 → 全量重置
      this._writeBase(workspace)
      this._writePatches([])
      safeSet(MODE_KEY, MODE_INCREMENTAL)
      if (this.writeLegacy) this._writeLegacy(workspace)
      return
    }

    const newPatches = diffWorkspace(lastState, workspace)
    if (newPatches.length === 0) {
      // 无变化：不动盘
      return
    }

    const merged = [...patches, ...newPatches]
    const estimated = serializePatches(merged).length
    if (merged.length > this.maxPatches || estimated > this.maxBytes) {
      this._writeBase(workspace)
      this._writePatches([])
    } else {
      this._writePatches(merged)
    }
    if (this.writeLegacy) this._writeLegacy(workspace)
  }

  compact(workspace?: PersistedWorkspace): void {
    const latest = workspace ?? this.load()
    if (!latest) return
    this._writeBase(latest)
    this._writePatches([])
    safeSet(MODE_KEY, MODE_INCREMENTAL)
    if (this.writeLegacy) this._writeLegacy(latest)
  }

  clear(): void {
    safeRemove(BASE_KEY)
    safeRemove(PATCHES_KEY)
    safeRemove(MODE_KEY)
    safeRemove(LEGACY_KEY)
  }

  stats(): IncrementalStats {
    const mode = safeGet(MODE_KEY)
    const base = safeGet(BASE_KEY)
    const patches = safeGet(PATCHES_KEY)
    const totalBytes = (base?.length ?? 0) + (patches?.length ?? 0)
    return {
      mode:
        mode === MODE_INCREMENTAL
          ? "incremental"
          : (safeGet(LEGACY_KEY) ? "full" : "empty"),
      baseBytes: base?.length ?? 0,
      patchesCount: this._readPatches().length,
      patchesBytes: patches?.length ?? 0,
      totalBytes,
    }
  }

  // ── 私有 ──
  private _readBase(): PersistedWorkspace | null {
    const raw = safeGet(BASE_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as PersistedWorkspace
    } catch {
      return null
    }
  }

  private _writeBase(w: PersistedWorkspace): void {
    safeSet(BASE_KEY, JSON.stringify(w))
  }

  private _readPatches(): PatchOp[] {
    return deserializePatches(safeGet(PATCHES_KEY))
  }

  private _writePatches(patches: readonly PatchOp[]): void {
    safeSet(PATCHES_KEY, serializePatches(patches))
  }

  private _readLegacy(): PersistedWorkspace | null {
    const raw = safeGet(LEGACY_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as PersistedWorkspace
    } catch {
      return null
    }
  }

  private _writeLegacy(w: PersistedWorkspace): void {
    safeSet(LEGACY_KEY, JSON.stringify(w))
  }
}

export const INCREMENTAL_MAX_PATCHES = DEFAULT_MAX_PATCHES
export const INCREMENTAL_MAX_BYTES = DEFAULT_MAX_BYTES
