/**
 * Workspace 持久化补丁（JSON Patch 子集）。
 *
 * 契约：
 *   - 只支持 "replace"（字段固定，变化即替换）
 *   - path 白名单：/version /boundary /name /kind /activeFile /expanded
 *   - 数组字段（expanded）整体 replace（不做 LCS 数组 diff）
 *   - 纯函数无副作用
 *
 * 不负责：
 *   - 存储（incremental store 管）
 *   - 序列化（JSON.stringify 调用方管）
 */
import type { PersistedWorkspace } from "./workspace_persistence_contract"

export interface PatchOp {
  op: "replace"
  path: string
  value: unknown
}

const ALLOWED_KEYS = new Set<string>([
  "version", "boundary", "name", "kind", "activeFile", "expanded",
])

export function diffWorkspace(
  oldW: PersistedWorkspace,
  newW: PersistedWorkspace,
): PatchOp[] {
  if (!oldW || !newW) return []
  const out: PatchOp[] = []
  for (const key of ALLOWED_KEYS) {
    const a = (oldW as Record<string, unknown>)[key]
    const b = (newW as Record<string, unknown>)[key]
    if (JSON.stringify(a) !== JSON.stringify(b)) {
      out.push({ op: "replace", path: "/" + key, value: b })
    }
  }
  return out
}

export function applyWorkspace(
  base: PersistedWorkspace,
  patches: readonly PatchOp[],
): PersistedWorkspace {
  const copy: Record<string, unknown> = JSON.parse(JSON.stringify(base))
  for (const p of patches) {
    if (!p || p.op !== "replace") continue
    const key = String(p.path || "").replace(/^\//, "")
    if (!ALLOWED_KEYS.has(key)) continue
    copy[key] = p.value
  }
  return copy as unknown as PersistedWorkspace
}

export function serializePatches(patches: readonly PatchOp[]): string {
  return JSON.stringify(patches)
}

export function deserializePatches(json: string | null): PatchOp[] {
  if (!json) return []
  try {
    const raw = JSON.parse(json)
    if (!Array.isArray(raw)) return []
    return raw.filter(
      (p) => p && p.op === "replace" && typeof p.path === "string",
    ) as PatchOp[]
  } catch {
    return []
  }
}

export const PERSIST_PATCH_KEYS = Array.from(ALLOWED_KEYS)
