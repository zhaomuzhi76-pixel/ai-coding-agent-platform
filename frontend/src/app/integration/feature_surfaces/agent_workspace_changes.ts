import type { DiffChange } from
  "../../product/workspace/diff/diff_review_contract"

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

function text(value: unknown): string | null {
  return typeof value === "string" ? value : null
}

function toChange(value: unknown): DiffChange | null {
  const item = asRecord(value)
  if (!item) return null
  const file = text(item.file) ?? text(item.path) ?? text(item.file_path)
  const before = text(item.before) ?? text(item.old) ?? text(item.old_content)
  const after = text(item.after) ?? text(item.new) ?? text(item.new_content)
  if (!file || before === null || after === null) return null
  return { file, before, after }
}

function collectChanges(value: unknown, depth = 0): DiffChange[] {
  if (depth > 8) return []

  if (Array.isArray(value)) {
    const direct = value
      .map(toChange)
      .filter((i): i is DiffChange => i !== null)
    if (direct.length > 0) return direct
    for (const item of value) {
      const nested = collectChanges(item, depth + 1)
      if (nested.length > 0) return nested
    }
    return []
  }

  const item = asRecord(value)
  if (!item) return []

  const direct = toChange(item)
  if (direct) return [direct]

  for (const key of [
    "changes", "modifications", "files",
    "proposal", "modification", "data",
    "output", "outputs", "result",
  ]) {
    const nested = collectChanges(item[key], depth + 1)
    if (nested.length > 0) return nested
  }
  return []
}

export function projectAgentWorkspaceChanges(
  result: unknown,
): readonly DiffChange[] {
  return collectChanges(result)
}

export function matchChangeForFile(
  changes: readonly DiffChange[],
  activeFile: string | null,
): DiffChange | null {
  if (!activeFile || changes.length === 0) return null
  const norm = (p: string) => p.replace(/\\/g, "/").replace(/^\/+/, "")
  const a = norm(activeFile)
  const aBase = a.split("/").filter(Boolean).pop() ?? a
  for (const c of changes) {
    const b = norm(c.file)
    if (b === a) return c
    if (b.endsWith("/" + a) || a.endsWith("/" + b)) return c
    const bBase = b.split("/").filter(Boolean).pop() ?? b
    if (bBase === aBase) return c
  }
  return null
}



export function joinPath(root: string, rel: string): string {
  if (!root) return rel
  const r = root.replace(/\/+$/, "")
  const p = rel.replace(/^\/+/, "")
  if (p.startsWith(r + "/") || p === r) return p
  return r + "/" + p
}

export async function applyChange(
  absPath: string,
  change: DiffChange,
  sessionId: string,
): Promise<boolean> {
  console.log('[applyChange] call', absPath, 'session', sessionId)
  try {
    let before = change.before
    try {
      const current = await readFile(absPath)
      if (current) before = current.content
    } catch {
      // 使用提案里的 before
    }
    await writeFile(absPath, change.after)
    await localPatchSave({
      sessionId,
      path: absPath,
      before,
      after: change.after,
      status: "accepted",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      error: null,
    })
    console.log("[applyChange] OK", absPath)
    return true
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    // eslint-disable-next-line no-alert
    window.alert(
      "[applyChange] FAILED\n\npath: " + absPath +
      "\n\nerror: " + msg
    )
    await localPatchSave({
      sessionId,
      path: absPath,
      before: change.before,
      after: change.after,
      status: "failed",
      createdAt: Date.now(),
      updatedAt: Date.now(),
      error: msg,
    })
    console.error("[applyChange] FAIL", absPath, err)
    return false
  }
}

export async function rejectChange(
  absPath: string,
  change: DiffChange,
  sessionId: string,
): Promise<void> {
  await localPatchSave({
    sessionId,
    path: absPath,
    before: change.before,
    after: change.after,
    status: "rejected",
    createdAt: Date.now(),
    updatedAt: Date.now(),
    error: null,
  })
  console.log("[rejectChange]", absPath)
}
