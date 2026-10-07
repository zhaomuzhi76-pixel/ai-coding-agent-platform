import { getDesktopRuntime } from "./desktop_runtime_access"
import type { MongoWorkspace, MongoNode } from "./desktop_runtime_contract"

const rt = () => getDesktopRuntime()

export async function mongoIsAvailable(): Promise<boolean> {
  const r = rt(); return r ? r.mongoIsAvailable() : false
}
export async function mongoSaveWorkspace(rootPath: string, rootName: string): Promise<MongoWorkspace | null> {
  const r = rt(); return r ? r.mongoSaveWorkspace(rootPath, rootName) : null
}
export async function mongoLoadWorkspace(rootPath: string): Promise<MongoWorkspace | null> {
  const r = rt(); return r ? r.mongoLoadWorkspace(rootPath) : null
}
export async function mongoListChildren(workspaceId: string, parentPath: string): Promise<MongoNode[]> {
  const r = rt(); return r ? r.mongoListChildren(workspaceId, parentPath) : []
}
export async function mongoSetExpanded(workspaceId: string, path: string, isExpanded: boolean): Promise<boolean> {
  const r = rt(); return r ? r.mongoSetExpanded(workspaceId, path, isExpanded) : false
}
export async function mongoListExpanded(workspaceId: string): Promise<string[]> {
  const r = rt(); return r ? r.mongoListExpanded(workspaceId) : []
}
export async function mongoIncrementalScan(workspaceId: string, rootPath: string, dirPath: string): Promise<number> {
  const r = rt(); return r ? r.mongoIncrementalScan(workspaceId, rootPath, dirPath) : 0
}
export async function mongoAgentEventAppend(sessionId: string, event: unknown): Promise<boolean> {
  const r = rt(); return r ? r.mongoAgentEventAppend(sessionId, event) : false
}
export async function mongoAgentEventList(sessionId: string, limit = 1000): Promise<unknown[]> {
  const r = rt(); return r ? r.mongoAgentEventList(sessionId, limit) : []
}
export async function mongoPatchSave(patch: unknown): Promise<string | null> {
  const r = rt(); return r ? r.mongoPatchSave(patch) : null
}
export async function mongoPatchStatus(patchId: string, status: string): Promise<boolean> {
  const r = rt(); return r ? r.mongoPatchStatus(patchId, status) : false
}
export async function mongoPatchList(sessionId: string): Promise<unknown[]> {
  const r = rt(); return r ? r.mongoPatchList(sessionId) : []
}
