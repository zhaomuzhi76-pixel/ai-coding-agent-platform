export interface PickedFolder { name: string; path: string }
export interface FsEntry { name: string; path: string; kind: "file" | "directory"; size: number }
export interface FileReadResult { path: string; content: string; size: number }
export interface FileWriteResult { path: string; size: number }

export interface MongoWorkspace { id: string; rootPath: string; rootName: string }
export interface MongoNode {
  _id: string; workspaceId: string; path: string; parentPath: string;
  name: string; kind: "file" | "directory"; size: number;
  mtime: string; contentHash: string | null; isExpanded: boolean;
}

export interface DesktopRuntime {
  selectFolder(): Promise<PickedFolder | null>
  allowRoot(root: string): Promise<boolean>
  listDir(dir: string): Promise<FsEntry[]>
  readFile(path: string): Promise<FileReadResult>
  writeFile(path: string, content: string): Promise<FileWriteResult>
  persistGet(key: string): Promise<unknown>
  persistSet(key: string, value: unknown): Promise<boolean>
  persistLogAppend(key: string, record: unknown): Promise<boolean>
  persistLogRead(key: string): Promise<unknown>
  mongoIsAvailable(): Promise<boolean>
  mongoSaveWorkspace(rootPath: string, rootName: string): Promise<MongoWorkspace | null>
  mongoLoadWorkspace(rootPath: string): Promise<MongoWorkspace | null>
  mongoListChildren(workspaceId: string, parentPath: string): Promise<MongoNode[]>
  mongoSetExpanded(workspaceId: string, path: string, isExpanded: boolean): Promise<boolean>
  mongoListExpanded(workspaceId: string): Promise<string[]>
  mongoIncrementalScan(workspaceId: string, rootPath: string, dirPath: string): Promise<number>
  mongoSessionUpsert(sessionId: string, payload: unknown): Promise<boolean>
  mongoAgentEventAppend(sessionId: string, event: unknown): Promise<boolean>
  mongoAgentEventList(sessionId: string, limit?: number): Promise<unknown[]>
  mongoPatchSave(patch: unknown): Promise<string | null>
  mongoPatchStatus(patchId: string, status: string): Promise<boolean>
  mongoPatchList(sessionId: string): Promise<unknown[]>
}

declare global {
  interface Window { desktopRuntime?: DesktopRuntime }
}
