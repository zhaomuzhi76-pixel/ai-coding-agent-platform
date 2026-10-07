
import type { SessionResponse } from "../../core/api/api_types"

export interface AgentWorkspaceSession {
  id: string
  sessionId: string
  projectId: string
  rootPath: string
}

export function mapAgentSession(
  value: SessionResponse,
): AgentWorkspaceSession {
  return {
    id: value.session_id,
    sessionId: value.session_id,
    projectId: value.project_id,
    rootPath: value.root_path,
  }
}
