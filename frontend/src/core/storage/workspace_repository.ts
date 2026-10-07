import { get, put } from "./indexed_db"

export interface WorkspaceRecord {
  rootPath: string
  rootName: string
  rootHash: string | null
  createdAt: number
  lastOpenedAt: number
}

export async function upsertWorkspace(
  rootPath: string,
  rootName: string,
): Promise<WorkspaceRecord> {
  const existing = await get<WorkspaceRecord>("workspaces", rootPath)
  const now = Date.now()
  const record: WorkspaceRecord = {
    rootPath,
    rootName,
    rootHash: existing?.rootHash ?? null,
    createdAt: existing?.createdAt ?? now,
    lastOpenedAt: now,
  }
  await put("workspaces", record)
  return record
}

export async function getWorkspace(rootPath: string): Promise<WorkspaceRecord | null> {
  return get<WorkspaceRecord>("workspaces", rootPath)
}

export async function setRootHash(rootPath: string, hash: string): Promise<void> {
  const ws = await getWorkspace(rootPath)
  if (!ws) return
  ws.rootHash = hash
  ws.lastOpenedAt = Date.now()
  await put("workspaces", ws)
}
