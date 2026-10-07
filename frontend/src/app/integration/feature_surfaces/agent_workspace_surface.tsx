import {
  useSyncExternalStore,
} from "react"

import type {
  AgentWorkspaceController,
} from "../../../features/agent_workspace/controllers/agent_workspace_controller"

import type {
  AgentWorkspaceStore,
} from "../../../features/agent_workspace/agent_workspace_store"

import {
  AgentWorkspaceView,
} from "../../../features/agent_workspace/ui/agent_workspace_view"

interface Props {
  store: AgentWorkspaceStore
  controller: AgentWorkspaceController
}

export function AgentWorkspaceSurface(
  props: Props,
) {
  const subscribe =
    props.store.subscribe.bind(
      props.store,
    )

  const getSnapshot =
    props.store.getSnapshot.bind(
      props.store,
    )

  const state =
    useSyncExternalStore(
      subscribe,
      getSnapshot,
      getSnapshot,
    )

  return (
    <AgentWorkspaceView
      state={state}
      controller={props.controller}
    />
  )
}
