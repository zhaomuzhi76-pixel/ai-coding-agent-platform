import {
  bulkDelete,
  bulkPut,
  put,
  queryIndex,
} from "./indexed_db"

export interface FileNodeRecord {
  id: string
  workspaceId: string
  path: string
  parentPath: string
  name: string
  kind: "file" | "directory"
  size: number
  mtime: number
  contentHash: string | null
  isExpanded: boolean
}

function makeId(workspaceId: string, path: string): string {
  return workspaceId + "::" + path
}

export async function listChildren(
  workspaceId: string,
  parentPath: string,
): Promise<FileNodeRecord[]> {
  const rows = await queryIndex<FileNodeRecord>("file_nodes", {
    index: "by_workspace_parent",
    key: [workspaceId, parentPath],
  })
  rows.sort((a, b) => {
    if (a.kind !== b.kind) return a.kind === "directory" ? -1 : 1
    return a.name.localeCompare(b.name)
  })
  return rows
}

export async function getNode(
  workspaceId: string,
  path: string,
): Promise<FileNodeRecord | null> {
  const rows = await queryIndex<FileNodeRecord>("file_nodes", {
    index: "by_workspace_path",
    key: [workspaceId, path],
  })
  return rows[0] ?? null
}

export async function setExpanded(
  workspaceId: string,
  path: string,
  isExpanded: boolean,
): Promise<void> {
  const node = await getNode(workspaceId, path)
  if (!node) return
  node.isExpanded = isExpanded
  await put("file_nodes", node)
}

export async function listExpanded(workspaceId: string): Promise<string[]> {
  const rows = await queryIndex<FileNodeRecord>("file_nodes", {
    index: "by_workspace_expanded",
    key: [workspaceId, 1],
  })
  return rows.map(r => r.path).sort()
}

export interface UpsertNodeInput {
  workspaceId: string
  path: string
  parentPath: string
  name: string
  kind: "file" | "directory"
  size: number
  mtime: number
  contentHash: string | null
}

export async function upsertNodes(inputs: UpsertNodeInput[]): Promise<void> {
  if (inputs.length === 0) return
  const existing = await Promise.all(
    inputs.map(i => getNode(i.workspaceId, i.path)),
  )
  const records: FileNodeRecord[] = inputs.map((input, index) => {
    const prev = existing[index]
    return {
      id: makeId(input.workspaceId, input.path),
      workspaceId: input.workspaceId,
      path: input.path,
      parentPath: input.parentPath,
      name: input.name,
      kind: input.kind,
      size: input.size,
      mtime: input.mtime,
      contentHash: input.contentHash,
      isExpanded: prev?.isExpanded ?? false,
    }
  })
  await bulkPut("file_nodes", records)
}

export async function deleteNodes(
  workspaceId: string,
  paths: string[],
): Promise<void> {
  if (paths.length === 0) return
  const ids = paths.map(p => makeId(workspaceId, p))
  await bulkDelete("file_nodes", ids)
}
