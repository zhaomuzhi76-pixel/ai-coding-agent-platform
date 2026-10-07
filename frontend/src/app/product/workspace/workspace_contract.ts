import type {
  AgentResourceBoundary,
} from "../../../core/resources/resource_boundary"

export interface WorkspaceCapability {
  name: string
}

export interface WorkspaceSnapshot {
  project: string | null
  activeFile: string | null
  activeFileSource?: import('./explorer/file_node_source').FileNodeSource | null
  resourceName: string | null
  resourceBoundary: AgentResourceBoundary | null
  capabilities: WorkspaceCapability[]
  fileVersion?: number
}

export interface WorkspaceFileHandle {
  readonly kind: "file"
  readonly name: string
  getFile(): Promise<File>
  createWritable?: () => Promise<{
    write(
      content: string,
    ): Promise<void> | void
    close(): Promise<void> | void
  }>
}

export interface WorkspaceDirectoryHandle {
  readonly kind: "directory"
  readonly name: string
  values(): AsyncIterableIterator<
    WorkspaceResourceHandle
  >
}

export type WorkspaceResourceHandle =
  | WorkspaceDirectoryHandle
  | WorkspaceFileHandle

