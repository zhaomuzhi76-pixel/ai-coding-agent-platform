import type {
  ApplicationPlugin,
} from "./plugin_contract"

import {
  PluginRegistry,
} from "./plugin_registry"

import {
  IndustrialControlPlaneEntry,
} from "../product/industrial/industrial_control_plane_entry"

import {
  PlatformWorkbenchEntry,
} from "../product/industrial/platform_workbench_entry"


const plugins: ApplicationPlugin[] = [
  {
    id: "industrial-control-plane",
    title: "Industrial Control Plane",
    render: IndustrialControlPlaneEntry,
  },
  {
    id: "platform-workbench",
    title: "AI Coding Platform",
    render: PlatformWorkbenchEntry,
  },
]


export function createApplicationPluginRegistry():
  PluginRegistry {
  const registry = new PluginRegistry()
  for (const plugin of plugins) {
    registry.register(plugin)
  }
  return registry
}
