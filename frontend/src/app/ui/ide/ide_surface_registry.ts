import type { ReactNode } from "react"
import type { WorkspaceSurfaceSlot } from "../contracts/workspace_surface_contract"

export interface IdeSurfaceContext {
  state: unknown
  store: unknown
  controller: unknown
  workspace?: unknown
}

export type IdeSurfaceRenderer = (
  context: IdeSurfaceContext,
) => ReactNode

export interface IdeDynamicSurfaceContract {
  slot: WorkspaceSurfaceSlot
  render: IdeSurfaceRenderer
}

export class IdeSurfaceRegistry {
  private readonly surfaces =
    new Map<WorkspaceSurfaceSlot, IdeSurfaceRenderer>()

  register(surface: IdeDynamicSurfaceContract) {
    this.surfaces.set(surface.slot, surface.render)
  }

  resolve(
    slot: WorkspaceSurfaceSlot,
    context: IdeSurfaceContext,
  ): ReactNode {
    const renderer = this.surfaces.get(slot)
    if (!renderer) {
      return null
    }
    return renderer(context)
  }

  snapshot() {
    return Array.from(this.surfaces.keys())
  }
}
