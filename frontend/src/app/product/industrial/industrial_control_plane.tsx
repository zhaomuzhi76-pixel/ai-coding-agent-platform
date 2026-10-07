import {
  useEffect,
  useRef,
  useSyncExternalStore,
} from "react"

import {
  createResourceBoundary,
} from "../../../core/resources/resource_boundary"

import type {
  AgentWorkspaceState,
} from "../../../features/agent_workspace/agent_workspace_state"

import type {
  AgentWorkspaceStore,
} from "../../../features/agent_workspace/agent_workspace_store"

import type {
  AgentWorkspaceController,
} from "../../../features/agent_workspace/controllers/agent_workspace_controller"

import type {
  ProjectSessionAgentWorkspaceBridge,
} from "../../../features/agent_workspace/context/project_session_agent_workspace_bridge"

import { useI18n } from "../../../core/i18n/i18n"

import {
  createIndustrialControlPlaneWorkspace,
} from "./composition/industrial_control_plane_composition"

import type {
  WorkspaceController,
} from "../workspace/workspace_controller"

import {
  buildRestoredLocalRoot,
} from "../workspace/explorer/local_folder_persistence"

import { bootstrapProjectSession } from "./industrial_session_bootstrap"
import { createProjectWorkspaceRoot } from "../workspace/explorer/project_workspace_file_source"

export interface IndustrialControlPlaneProps {
  state: AgentWorkspaceState
  store: AgentWorkspaceStore
  controller: AgentWorkspaceController
  workspaceController: WorkspaceController
  bridge: ProjectSessionAgentWorkspaceBridge
  active?: boolean
}

function basename(p: string): string {
  const segs = p.replace(/\\/g, "/").split("/").filter(Boolean)
  return segs.length > 0 ? segs[segs.length - 1] : p
}

export function IndustrialControlPlane(
  props: IndustrialControlPlaneProps,
) {
  const { locale } = useI18n()
  const lastSyncedRoot = useRef<string | null>(null)

  const workspace = useSyncExternalStore(
    props.workspaceController.store.subscribe.bind(
      props.workspaceController.store,
    ),
    props.workspaceController.store.getSnapshot.bind(
      props.workspaceController.store,
    ),
    props.workspaceController.store.getSnapshot.bind(
      props.workspaceController.store,
    ),
  )

  // 1. 启动时还原本地 root
  useEffect(() => {
    let cancelled = false
    void (async () => {
      // URL 参数优先：?workspace=/path/to/project
      const hashQuery =
        window.location.hash.split("?")[1] ?? ""
      const urlWs = new URLSearchParams(hashQuery).get("workspace")
      if (urlWs) {
        const name = basename(urlWs)
        const boundary = createResourceBoundary({
          projectId: null,
          workspace: urlWs,
          targetPath: ".",
          targetKind: "directory",
        })
        await props.workspaceController.openResource(
          boundary,
          name,
          null,
          null,
        )
        return
      }
      // 回退：localStorage 恢复
      const restored = await buildRestoredLocalRoot()
      if (cancelled || !restored) return
      const boundary = createResourceBoundary({
        projectId: null,
        workspace: restored.path,
        targetPath: ".",
        targetKind: "directory",
      })
      await props.workspaceController.openResource(
        boundary,
        restored.name,
        restored.root,
        null,
      )
    })()
    return () => { cancelled = true }
  }, [props.workspaceController])

  // 2. workspace root 就绪后自动注册项目 + 创建 session
  useEffect(() => {
    const root = workspace.resourceBoundary?.workspace
    if (!root) return
    if (lastSyncedRoot.current === root) return
    lastSyncedRoot.current = root

    const name = workspace.resourceName ?? basename(root)
    let cancelled = false

    void (async () => {
      try {
        const result = await bootstrapProjectSession(root, name)
        if (cancelled) return
        // 用 projectId 构造真实 root 并挂到 fileTree
        const projectRoot = createProjectWorkspaceRoot(
          result.projectId, name,
        )
        props.workspaceController.fileTreeStore.setFiles([projectRoot])
        // 把 projectId 写回 boundary，持久化
        const newBoundary = createResourceBoundary({
          projectId: result.projectId,
          workspace: root,
          targetPath: ".",
          targetKind: "directory",
        })
        props.workspaceController.store.setResource(
          newBoundary, name, null, null,
        )
        await props.controller.selectSession(result.sessionId)
      } catch (err) {
        lastSyncedRoot.current = null
        console.error("[session bootstrap] failed:", err)
      }
    })()

    return () => { cancelled = true }
  }, [
    workspace.resourceBoundary?.workspace,
    workspace.resourceName,
    props.controller,
  ])

  return createIndustrialControlPlaneWorkspace({
    state: props.state,
    store: props.store,
    controller: props.controller,
    workspaceController: props.workspaceController,
    bridge: props.bridge,
    locale,
    resourceBoundary: workspace.resourceBoundary,
    selectedName:
      workspace.activeFile
      ?? (
        workspace.resourceBoundary?.targetKind === "file"
          ? workspace.resourceBoundary.targetPath
          : null
      )
      ?? workspace.resourceName,
    activeFileSource: workspace.activeFileSource ?? null,
  })
}
