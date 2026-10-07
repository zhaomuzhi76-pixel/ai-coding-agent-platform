import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react"

import type {
  Locale,
} from "../../../../../core/i18n/locale"

import type {
  AgentResourceBoundary,
} from "../../../../../core/resources/resource_boundary"

import {
  createIdeSurfaceComposition,
} from "../../../../integration/composition/ide_surface_composition"

import {
  IndustrialCodexWorkspace,
} from "../../../../ui/ide/industrial_codex_workspace"

import type {
  AgentWorkspaceState,
} from "../../../../../features/agent_workspace/agent_workspace_state"

import type {
  AgentWorkspaceStore,
} from "../../../../../features/agent_workspace/agent_workspace_store"






export interface IndustrialControlPlaneWorkspaceProps {
  state: AgentWorkspaceState
  store: AgentWorkspaceStore
  controller: AgentWorkspaceController
  workspaceController: WorkspaceController
  bridge: ProjectSessionAgentWorkspaceBridge
  locale: Locale
  resourceBoundary: AgentResourceBoundary | null
  selectedName: string | null
  activeFileSource: import(
    "../../workspace/explorer/file_node_source"
  ).FileNodeSource | null
}

export interface IndustrialControlPlaneComposition {
  workspaceId: string
  render(
    props: IndustrialControlPlaneWorkspaceProps,
  ): ReactNode
}
