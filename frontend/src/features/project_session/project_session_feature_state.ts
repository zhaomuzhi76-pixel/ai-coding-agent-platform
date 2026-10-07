import type {
  ProjectResponse,
  SessionResponse,
} from "./contracts/project_session_contract"

export type ProjectFeaturePhase =
  | "idle"
  | "loading"
  | "ready"
  | "error"

export interface ProjectSessionFeatureState {
  phase: ProjectFeaturePhase
  project: ProjectResponse | null
  session: SessionResponse | null
  error: string | null
  revision: number
}

export const initialProjectSessionFeatureState:
  ProjectSessionFeatureState = {
    phase: "idle",
    project: null,
    session: null,
    error: null,
    revision: 0,
  }
