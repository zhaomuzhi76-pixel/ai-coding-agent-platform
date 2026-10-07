import type {
  PlatformProposal,
} from "../../../core/contracts/platform"
import type { PlatformGateway } from "../platform_gateway"
import {
  initialPlatformState,
  type PlatformState,
} from "../platform_state"

export type PlatformListener = () => void

interface MutationResult {
  proposal: PlatformProposal
}
