import type { FileNodeSource } from "./file_node_source"

export interface WorkspaceResourceEntry {

  name: string

  type:
    | "file"
    | "directory"

  source?: FileNodeSource

  loadChildren?: () => Promise<WorkspaceResourceEntry[]>

  handle?: unknown

}
