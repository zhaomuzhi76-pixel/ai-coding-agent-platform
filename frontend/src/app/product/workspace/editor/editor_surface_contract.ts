import type {
  FileNodeSource,
} from "../explorer/file_node_source"

export interface EditorPendingChange {
  before: string
  after: string
  onApprove?: () => void
  onReject?: () => void
}

export interface EditorSurfaceProps {
  activeFile: string | null
  activeFileSource: FileNodeSource | null
  pendingChange?: EditorPendingChange | null
  fileVersion?: number
}
