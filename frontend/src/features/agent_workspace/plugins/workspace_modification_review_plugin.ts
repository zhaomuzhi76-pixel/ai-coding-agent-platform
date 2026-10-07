import type {
  AgentRuntimeCapability,
} from "../runtime/agent_runtime_capability_contract"

export const WorkspaceModificationReviewPlugin:
  AgentRuntimeCapability = {
    id: "workspace.modification_review",
    enabled: true,
  }

export const MODIFICATION_REVIEW_EVENTS = [
  "modification.started",
  "modification.planned",
  "modification.executed",
  "modification.verification_failed",
  "modification.rollback",
  "modification.completed",
] as const
