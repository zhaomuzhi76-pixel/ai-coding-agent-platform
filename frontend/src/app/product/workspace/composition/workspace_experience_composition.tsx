import type { ReactElement } from "react"
import { EditorSurface } from "../editor/editor_surface"
import { TerminalSurface } from "../terminal/terminal_surface"
import { CommandPalette } from "../command/command_palette"
import type { EditorPendingChange } from "../editor/editor_surface_contract"

export interface WorkspaceExperienceSurfaces {
  code: ReactElement
  terminal: ReactElement
  command: ReactElement
}

export interface WorkspaceExperienceContext {
  project: string | null
  activeFile: string | null
  activeFileSource?: import("../explorer/file_node_source").FileNodeSource | null
  agentSession: string | null
  pendingChange?: EditorPendingChange | null
  fileVersion?: number
}

export function createWorkspaceExperienceSurfaces(
  context: WorkspaceExperienceContext,
): WorkspaceExperienceSurfaces {
  const version = context.fileVersion ?? 0
  const activeFile = context.activeFile ?? ""
  // key 用 activeFile + fileVersion 组合：
  //   - 切文件 → key 变 → 重新挂载
  //   - bumpFileVersion → key 变 → 重新挂载 → useEditorDocument 重新 readFile
  const editorKey = `${activeFile}::${version}`

  return {
    code: (
      <EditorSurface
        key={editorKey}
        activeFile={context.activeFile}
        activeFileSource={context.activeFileSource ?? null}
        pendingChange={context.pendingChange ?? null}
        fileVersion={version}
      />
    ),
    terminal: <TerminalSurface />,
    command: <CommandPalette />,
  }
}
