import type {
  CodeIntelligenceRequest,
  CodeIntelligenceResult,
} from "../../core/api/code_intelligence_api"

export type CodeIntelligenceFeaturePhase =
  | "idle"
  | "loading"
  | "ready"
  | "error"

export interface CodeIntelligenceFeatureState {
  phase: CodeIntelligenceFeaturePhase
  request: CodeIntelligenceRequest | null
  result: CodeIntelligenceResult | null
  error: string | null
  revision: number
}

export const initialCodeIntelligenceFeatureState:
  CodeIntelligenceFeatureState = {
  phase: "idle",
  request: null,
  result: null,
  error: null,
  revision: 0,
}
