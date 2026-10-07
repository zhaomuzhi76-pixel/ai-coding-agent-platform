import {
  ProjectSessionAgentWorkspaceBridge,
} from "../../../features/agent_workspace/context/project_session_agent_workspace_bridge"

import {
  AgentWorkspaceStore,
} from "../../../features/agent_workspace/agent_workspace_store"

import {
  createAgentWorkspaceController,
} from "../../../features/agent_workspace/controllers/agent_workspace_controller_factory"

import {
  ProjectSessionFeatureController,
} from "../../../features/project_session/project_session_feature_controller"

import {
  WorkspaceBootstrap,
} from "../../product/workspace/workspace_bootstrap"

import {
  WorkspaceController,
} from "../../product/workspace/workspace_controller"
import { runIndustrialBootRestore } from "../../product/industrial/industrial_boot_restore"


export interface ControlPlaneCapability {
  projectSession: ProjectSessionFeatureController
  agentWorkspaceStore: AgentWorkspaceStore
  agentWorkspaceController:
    ReturnType<typeof createAgentWorkspaceController>["controller"]
  bridge: ProjectSessionAgentWorkspaceBridge
  workspaceBootstrap: WorkspaceBootstrap
  workspaceController: WorkspaceController
}

export function createControlPlaneCapability():
  ControlPlaneCapability {
  const projectSession =
    new ProjectSessionFeatureController()

  const {
    store: agentWorkspaceStore,
    controller: agentWorkspaceController,
  } =
    createAgentWorkspaceController()

  const bridge =
    new ProjectSessionAgentWorkspaceBridge(
      projectSession,
      agentWorkspaceStore,
    )


  const workspaceController =
    new WorkspaceController()

  const workspaceBootstrap =
    new WorkspaceBootstrap()

  // 启动时自动恢复 workspace + session（fire-and-forget）
  void runIndustrialBootRestore({
    workspaceController,
    projectSession,
    agentWorkspace: agentWorkspaceStore,
  }).catch((err) => {
    console.warn("BOOT_RESTORE_FAIL", err)
  })


  return {
    projectSession,
    agentWorkspaceStore,
    agentWorkspaceController,
    bridge,
    workspaceBootstrap,
    workspaceController,
  }
}

export function createControlPlaneComposition():
  ControlPlaneCapability {
  return createControlPlaneCapability()
}
