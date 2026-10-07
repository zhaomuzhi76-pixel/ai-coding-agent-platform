import type {
  AgentResourceBoundary,
} from "../../../core/resources/resource_boundary"

export type PersistedNodeType =
  | "directory"
  | "file"
export interface PersistedWorkspace {
  [key: string]: unknown
  version?: number
  boundary: AgentResourceBoundary
  name: string
  kind: PersistedNodeType
  activeFile: string | null
  expanded: string[]
}
