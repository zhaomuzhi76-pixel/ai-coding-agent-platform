import {
  useMemo,
} from "react"

import {
  createApplicationPluginRegistry,
} from "../plugins/application_plugins"

import {
  useControlPlaneContext,
} from "./context/control_plane_context"

import {
  AppShell,
} from "../ui/shell/app_shell"
import {
  GlobalNav,
} from "../ui/shell/global_nav"
import {
  ViewRouter,
} from "./view_router"

export function ApplicationSurface() {
  const capability = useControlPlaneContext()
  const registry = useMemo(
    () => createApplicationPluginRegistry(),
    [],
  )
  const codingPlugin = registry.resolve("industrial-control-plane")

  if (!codingPlugin) {
    throw new Error(
      "application plugin missing: industrial-control-plane",
    )
  }

  return (
    <AppShell>
      <GlobalNav />
      <div className="app-shell__body">
        <ViewRouter
          capability={{
            agentWorkspaceStore: capability.agentWorkspaceStore,
            agentWorkspaceController:
              capability.agentWorkspaceController,
            workspaceController: capability.workspaceController,
            bridge: capability.bridge,
          }}
          codingPlugin={codingPlugin}
        />
      </div>
    </AppShell>
  )
}
