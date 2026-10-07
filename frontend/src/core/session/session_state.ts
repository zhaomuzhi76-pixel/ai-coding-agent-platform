import type {
  SessionResponse,
} from "../api/api_types"

export type SessionPhase =
  | "idle"
  | "loading"
  | "ready"
  | "starting"
  | "active"
  | "closing"
  | "closed"
  | "removing"
  | "removed"
  | "error"

export interface SessionError {
  message: string
  status?: number
}

export interface ProjectSessionState {
  phase: SessionPhase
  session: SessionResponse | null
  error: SessionError | null
  requestId: number
}
