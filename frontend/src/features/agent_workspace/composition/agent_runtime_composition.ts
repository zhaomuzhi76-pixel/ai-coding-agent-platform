import {
  AgentRuntimeRegistry,
} from "../runtime/agent_runtime_registry"

import {
  WorkspaceFilePlugin,
} from "../plugins/workspace_file_plugin"

import {
  WorkspaceTerminalPlugin,
} from "../plugins/workspace_terminal_plugin"

import {
  WorkspaceDiffPlugin,
} from "../plugins/workspace_diff_plugin"


export function createAgentRuntimeComposition(){

  const registry =
    new AgentRuntimeRegistry()


  registry.register(
    WorkspaceFilePlugin,
  )

  registry.register(
    WorkspaceTerminalPlugin,
  )

  registry.register(
    WorkspaceDiffPlugin,
  )


  return {
    registry,
  }

}
