import type {
  PlatformDomainInfo,
  PlatformModelOption,
  PlatformProposal,
  PlatformSession,
} from "../../core/contracts/platform"

export type PlatformPhase =
  | "idle"
  | "loading_catalog"
  | "ready"
  | "working"
  | "error"

export interface PlatformState {
  phase: PlatformPhase
  session: PlatformSession | null
  proposals: PlatformProposal[]
  activeProposalId: string | null
  models: PlatformModelOption[]
  domains: PlatformDomainInfo[]
  selectedModel: string
  selectedDomain: string
  message: string
  error: string | null
  stageCursor: number
}

export const initialPlatformState: PlatformState = {
  phase: "idle",
  session: null,
  proposals: [],
  activeProposalId: null,
  models: [],
  domains: [],
  selectedModel: "",
  selectedDomain: "",
  message: "",
  error: null,
  stageCursor: 0,
}
