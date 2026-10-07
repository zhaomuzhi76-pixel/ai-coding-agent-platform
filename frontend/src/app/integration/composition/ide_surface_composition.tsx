import { useSyncExternalStore } from "react"

import {
  IdeSurfaceRegistry,
} from "../../ui/ide/ide_surface_registry"

import {
  createWorkspaceExperienceSurfaces,
} from "../../product/workspace/composition/workspace_experience_composition"

import type {
  WorkspaceExperienceContext,
} from "../../product/workspace/composition/workspace_experience_composition"

import type {
  AgentWorkspaceStore,
} from "../../../features/agent_workspace/agent_workspace_store"

import type {
  AgentWorkspaceController,
} from "../../../features/agent_workspace/controllers/agent_workspace_controller"

import {
  ExecutionTimelinePanel,
} from "../../../features/agent_workspace/events/ui/execution_timeline_panel"

import {
  AgentWorkspaceSurface,
} from "../feature_surfaces/agent_workspace_surface"

import {
  AgentWorkspaceReviewSurface,
} from "../feature_surfaces/agent_workspace_review_surface"

import {
  FileTreeView,
} from "../../product/workspace/explorer/file_tree_view"

import type {
  WorkspaceController,
} from "../../product/workspace/workspace_controller"

import {
  pickLocalWorkspace,
  desktopRuntimeAvailable,
} from "../../product/industrial/industrial_folder_picker"

import {
  createResourceBoundary,
} from "../../../core/resources/resource_boundary"

function ExecutionSurface(
  props: { store: AgentWorkspaceStore },
) {
  const subscribe = props.store.subscribe.bind(props.store)
  const getSnapshot = props.store.getSnapshot.bind(props.store)
  const state = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getSnapshot,
  )
  return (
    <ExecutionTimelinePanel messages={state.messages} />
  )
}

function SidebarSurface(
  props: { workspace: WorkspaceController },
) {
  const subscribe =
    props.workspace.store.subscribe.bind(
      props.workspace.store,
    )
  const getSnapshot =
    props.workspace.store.getSnapshot.bind(
      props.workspace.store,
    )
  const snapshot = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getSnapshot,
  )

  const available = desktopRuntimeAvailable()

  const onOpenFolder = async () => {
    const picked = await pickLocalWorkspace()
    if (!picked) {
      return
    }
    const boundary = createResourceBoundary({
      projectId: null,
      workspace: picked.folder.path,
      targetPath: ".",
      targetKind: "directory",
    })
    await props.workspace.openResource(
      boundary,
      picked.folder.name,
      picked.root,
      null,
    )
  }

  return (
    <div className="ws-sidebar-surface">
      <button
        type="button"
        className="ws-sidebar-open"
        data-testid="workspace-open-folder"
        disabled={!available}
        onClick={() => void onOpenFolder()}
      >
        Open Folder
      </button>
      {!available ? (
        <div
          className="ws-sidebar-hint"
          data-testid="workspace-desktop-hint"
        >
          Desktop runtime unavailable. Run via
          <code> npm run desktop</code> to open folders.
        </div>
      ) : null}
      <div className="ws-sidebar-tree">
        <FileTreeView
          store={props.workspace.fileTreeStore}
          activeFile={snapshot.activeFile}
          onOpenFile={(node, path) => {
            void props.workspace.openFile(
              path,
              node.source,
            )
          }}
        />
      </div>
    </div>
  )
}

export function createIdeSurfaceComposition(
  context: WorkspaceExperienceContext,
) {
  const workspaceSurfaces =
    createWorkspaceExperienceSurfaces({
      ...context,
      pendingChange: context.pendingChange ?? null,
    })

  const registry = new IdeSurfaceRegistry()

  registry.register({
    slot: "sidebar",
    render(surfaceContext) {
      const workspace =
        surfaceContext.workspace as
          | WorkspaceController
          | null
      if (!workspace) {
        return null
      }
      return <SidebarSurface workspace={workspace} />
    },
  })

  registry.register({
    slot: "code",
    render() {
      return workspaceSurfaces.code
    },
  })

  registry.register({
    slot: "prompt",
    render(surfaceContext) {
      const store =
        surfaceContext.store as AgentWorkspaceStore
      const controller =
        surfaceContext.controller as AgentWorkspaceController
      return (
        <AgentWorkspaceSurface
          store={store}
          controller={controller}
        />
      )
    },
  })

  registry.register({
    slot: "execution",
    render(surfaceContext) {
      const store =
        surfaceContext.store as AgentWorkspaceStore
      return <ExecutionSurface store={store} />
    },
  })

  registry.register({
    slot: "command",
    render() {
      return workspaceSurfaces.command
    },
  })

  registry.register({
    slot: "terminal",
    render() {
      return workspaceSurfaces.terminal
    },
  })

  registry.register({
    slot: "review",
    render() {
      return <AgentWorkspaceReviewSurface />
    },
  })

  return registry
}
