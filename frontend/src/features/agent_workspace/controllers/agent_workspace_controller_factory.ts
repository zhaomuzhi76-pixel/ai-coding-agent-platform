import {
  AgentWorkspaceController,
} from "./agent_workspace_controller"

import {
  AgentWorkspaceStore,
} from "../agent_workspace_store"

import {
  defaultAgentWorkspaceGateway,
} from "../agent_workspace_gateway"


export function createAgentWorkspaceController(
) {
  const store =
    new AgentWorkspaceStore(
      defaultAgentWorkspaceGateway,
    )

  return {
    store,
    controller:
      new AgentWorkspaceController(
        store,
      ),
  }
}
