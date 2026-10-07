export type ProjectSessionStatus =
  | "created"
  | "ready"
  | "active"
  | "closed"
  | "removed"

export interface ProjectSessionRef {
  session_id: string
  project_id: string
}

export function requireSessionId(
  sessionId: string,
): string {
  if (
    typeof sessionId !== "string"
    || !sessionId.trim()
  ) {
    throw new Error("session id required")
  }

  return sessionId.trim()
}
