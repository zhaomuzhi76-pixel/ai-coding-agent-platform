import type {
  AgentWorkspaceState,
} from "../../../../features/agent_workspace/agent_workspace_state"

import type {
  AgentResourceBoundary,
} from "../../../../core/resources/resource_boundary"


export interface AgentWorkspaceCapability {

  snapshot():
    AgentWorkspaceState


  openProject(
    projectId: string,
    boundary: AgentResourceBoundary,
  ): Promise<void>

}
