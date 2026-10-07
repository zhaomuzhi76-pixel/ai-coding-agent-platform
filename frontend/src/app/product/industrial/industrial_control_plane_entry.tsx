import { useEffect } from "react"

import {
  IndustrialControlPlane,
} from "./industrial_control_plane"

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

import type {
  WorkspaceController,
} from "../workspace/workspace_controller"

import {
  consumePendingFile,
} from "../../../features/platform/ui/coding_bridge"

export interface IndustrialControlPlaneEntryProps {
  state: AgentWorkspaceState
  store: AgentWorkspaceStore
  controller: AgentWorkspaceController
  workspaceController: WorkspaceController
  bridge: ProjectSessionAgentWorkspaceBridge
}

export function IndustrialControlPlaneEntry(
  props: IndustrialControlPlaneEntryProps,
) {
  // 从 platform Tab 切过来时，消费 pending openFile
  useEffect(() => {
    const path = consumePendingFile()
    if (!path) return
    void Promise.resolve(
      props.workspaceController.openFile(path),
    ).catch((err) => {
      console.warn("[pending.openFile] open failed", path, err)
    })
  }, [props.workspaceController])

  return (
    <IndustrialControlPlane
      state={props.state}
      store={props.store}
      controller={props.controller}
      workspaceController={props.workspaceController}
      active={true}
      bridge={props.bridge}
    />
  )
}
