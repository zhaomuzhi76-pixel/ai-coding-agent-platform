import type { ReactNode } from "react"

export type WorkspaceSurfaceSlot =
  | "sidebar"
  | "prompt"
  | "runtime"
  | "code"
  | "context"
  | "execution"
  | "terminal"
  | "review"
  | "command"
  | "extension"

export interface WorkspaceSurfaceContract {
  slot: WorkspaceSurfaceSlot
  content: ReactNode
}
