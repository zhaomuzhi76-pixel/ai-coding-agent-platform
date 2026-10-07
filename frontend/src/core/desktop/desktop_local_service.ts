import {
  upsertWorkspace,
  getWorkspace,
} from "../storage/workspace_repository"
import {
  listChildren,
  setExpanded,
  listExpanded,
  getNode,
} from "../storage/file_node_repository"
import type { FileNodeRecord } from "../storage/file_node_repository"
import { scanDirectory } from "../storage/local_scan"
import {
  appendEvent,
  listEvents,
  savePatch,
  listPatches,
} from "../storage/agent_repository"

export type { FileNodeRecord }

export async function localSaveWorkspace(
  rootPath: string,
  rootName: string,
): Promise<{ id: string; rootPath: string; rootName: string }> {
  const ws = await upsertWorkspace(rootPath, rootName)
  return { id: ws.rootPath, rootPath: ws.rootPath, rootName: ws.rootName }
}

export async function localLoadWorkspace(
  rootPath: string,
): Promise<{ id: string; rootPath: string; rootName: string } | null> {
  const ws = await getWorkspace(rootPath)
  if (!ws) return null
  return { id: ws.rootPath, rootPath: ws.rootPath, rootName: ws.rootName }
}

export async function localListChildren(
  workspaceId: string,
  parentPath: string,
): Promise<FileNodeRecord[]> {
  return listChildren(workspaceId, parentPath)
}

export async function localGetNode(
  workspaceId: string,
  path: string,
): Promise<FileNodeRecord | null> {
  return getNode(workspaceId, path)
}

export async function localSetExpanded(
  workspaceId: string,
  path: string,
  isExpanded: boolean,
): Promise<boolean> {
  await setExpanded(workspaceId, path, isExpanded)
  return true
}

export async function localListExpanded(workspaceId: string): Promise<string[]> {
  return listExpanded(workspaceId)
}

export async function localIncrementalScan(
  workspaceId: string,
  rootPath: string,
  dirPath: string,
): Promise<number> {
  const r = await scanDirectory(workspaceId, rootPath, dirPath)
  return r.scanned + r.removed
}

export async function localAgentEventAppend(
  sessionId: string,
  kind: string,
  payload: unknown,
): Promise<boolean> {
  await appendEvent({ sessionId, ts: Date.now(), kind, payload })
  return true
}

export async function localAgentEventList(
  sessionId: string,
): Promise<unknown[]> {
  return listEvents(sessionId)
}

export async function localPatchSave(patch: unknown): Promise<number> {
  return savePatch(patch as Parameters<typeof savePatch>[0])
}

export async function localPatchList(sessionId: string): Promise<unknown[]> {
  return listPatches(sessionId)
}
