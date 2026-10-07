import { listDir } from "../desktop/desktop_runtime"
import type { FsEntry } from "../desktop/desktop_runtime_contract"
import {
  listChildren,
  upsertNodes,
  deleteNodes,
  getNode,
} from "./file_node_repository"
import { getWorkspace, setRootHash } from "./workspace_repository"

const SKIP = new Set([
  "node_modules", ".git", ".cache",
  "dist", "build", "release",
])

function relPath(rootPath: string, absPath: string): string {
  const r = absPath.replace(/\\/g, "/")
  const root = rootPath.replace(/\\/g, "/").replace(/\/+$/, "")
  if (r === root) return "."
  if (r.startsWith(root + "/")) return r.slice(root.length + 1)
  return r
}

async function computeChildrenHash(
  rows: Array<{ path: string; contentHash: string | null; mtime: number }>,
): Promise<string> {
  const input = rows
    .map(r => r.path + "|" + (r.contentHash ?? "") + "|" + r.mtime)
    .sort()
    .join("\n")
  const buf = new TextEncoder().encode(input)
  const digest = await crypto.subtle.digest("SHA-1", buf)
  return Array.from(new Uint8Array(digest))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("")
}

export interface ScanResult {
  skipped: boolean
  scanned: number
  removed: number
}

export async function scanDirectory(
  workspaceId: string,
  rootPath: string,
  dirAbsPath: string,
): Promise<ScanResult> {
  const parentPath =
    dirAbsPath === rootPath ? "." : relPath(rootPath, dirAbsPath)

  const dbChildren = await listChildren(workspaceId, parentPath)
  const storedHash = parentPath === "."
    ? (await getWorkspace(rootPath))?.rootHash ?? null
    : (await getNode(workspaceId, parentPath))?.contentHash ?? null

  let entries: FsEntry[]
  try {
    entries = await listDir(dirAbsPath)
  } catch {
    return { skipped: false, scanned: 0, removed: 0 }
  }

  const filtered = entries.filter(e => !SKIP.has(e.name))
  const currentPaths = new Set(filtered.map(e => relPath(rootPath, e.path)))

  if (storedHash && dbChildren.length === filtered.length) {
    const allMatch = dbChildren.every(c => currentPaths.has(c.path))
    if (allMatch) return { skipped: true, scanned: 0, removed: 0 }
  }

  const now = Date.now()
  const inputs = filtered.map(e => ({
    workspaceId,
    path: relPath(rootPath, e.path),
    parentPath,
    name: e.name,
    kind: e.kind,
    size: e.size,
    mtime: now,
    contentHash: e.kind === "file" ? "size:" + e.size : null,
  }))

  await upsertNodes(inputs)

  const stale = dbChildren
    .filter(c => !currentPaths.has(c.path))
    .map(c => c.path)
  await deleteNodes(workspaceId, stale)

  const refreshed = await listChildren(workspaceId, parentPath)
  const newHash = await computeChildrenHash(
    refreshed.map(r => ({
      path: r.path,
      contentHash: r.contentHash,
      mtime: r.mtime,
    })),
  )

  if (parentPath === ".") {
    await setRootHash(rootPath, newHash)
  } else {
    const node = await getNode(workspaceId, parentPath)
    if (node) {
      await upsertNodes([{
        workspaceId: node.workspaceId,
        path: node.path,
        parentPath: node.parentPath,
        name: node.name,
        kind: node.kind,
        size: node.size,
        mtime: node.mtime,
        contentHash: newHash,
      }])
    }
  }

  return { skipped: false, scanned: inputs.length, removed: stale.length }
}
