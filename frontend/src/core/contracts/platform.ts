export interface PlatformSession {
  session_id: string
  workspace: string
  user_id: string
  locale: string
  model: string
  turn_count?: number
}

export interface PlatformModelOption {
  model: string
  provider: string
  display_name: string
  context_window: number
  supports_tool_call: boolean
  supports_stream: boolean
  supports_embedding: boolean
  cost_input_per_1k: number
  cost_output_per_1k: number
  strengths: string[]
}

export interface PlatformDomainInfo {
  name: string
  entity_types: string[]
  terms: number
}

export interface PlatformChange {
  file: string
  kind: string
  text: string
}

export type PlatformProposalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "applied"
  | "failed"
  | "rolled_back"

export interface PlatformProposal {
  proposal_id: string
  task: string
  plan: string
  changes: PlatformChange[]
  attempts: number
  status: PlatformProposalStatus
  file_count: number
  created_at: number
  updated_at: number
  error: string
}

export interface PlatformStageId {
  id: "propose" | "approve" | "apply" | "verify" | "learn"
  label: string
}
