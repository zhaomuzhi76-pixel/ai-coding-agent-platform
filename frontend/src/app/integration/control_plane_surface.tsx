import { IndustrialCodexWorkspace } from "../ui/ide/industrial_codex_workspace"
import type { IdeSurfaceRegistry } from "../ui/ide/ide_surface_registry"
import type { ControlPlaneCapability } from "./composition/control_plane_composition"

interface Props {
  controlPlane: unknown
  ide: {
    registry: IdeSurfaceRegistry
  }
}

export function ControlPlaneSurface(props: Props) {
  const capability =
    props.controlPlane as ControlPlaneCapability | null

  return (
    <IndustrialCodexWorkspace
      surfaces={props.ide.registry}
      workspace={capability?.workspaceController ?? null}
    />
  )
}
