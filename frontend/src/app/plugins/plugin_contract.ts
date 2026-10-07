import type {
  ComponentType,
} from "react"

import type {
  AgentWorkspaceState,
} from "../../features/agent_workspace/agent_workspace_state"

import type {
  AgentWorkspaceStore,
} from "../../features/agent_workspace/agent_workspace_store"

import type {
  AgentWorkspaceController,
} from "../../features/agent_workspace/controllers/agent_workspace_controller"

import type {
  ProjectSessionAgentWorkspaceBridge,
} from "../../features/agent_workspace/context/project_session_agent_workspace_bridge"

import type {
  WorkspaceController,
} from "../product/workspace/workspace_controller"

export interface ApplicationPluginProps {
  state: AgentWorkspaceState
  store: AgentWorkspaceStore
  controller: AgentWorkspaceController
  workspaceController: WorkspaceController
  bridge: ProjectSessionAgentWorkspaceBridge
}

export interface ApplicationPlugin {
  id: string
  title: string
  render: ComponentType<ApplicationPluginProps>
}

export interface PluginRegistryContract {
  register(plugin: ApplicationPlugin): void
  resolve(id: string): ApplicationPlugin | null
  all(): readonly ApplicationPlugin[]
  ready(): boolean
}
