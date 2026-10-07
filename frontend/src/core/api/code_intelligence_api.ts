import {
  request,
} from "../http/http_client"

export type CodeIntelligenceOperation =
  | "project"
  | "summary"
  | "file"
  | "analysis"
  | "impact"
  | "context"
  | "index"

export interface CodeIntelligenceRequest {
  query: string
  workspace?: string
  path?: string
  metadata?: Record<string, unknown>
}

export interface CodeIntelligenceFinding {
  [key: string]: unknown
}

export interface CodeIntelligenceResult {
  name: string
  findings: CodeIntelligenceFinding[]
  metadata: Record<string, unknown>
  ready: boolean
}

export const codeIntelligenceApi = {
  inspect(
    payload: CodeIntelligenceRequest,
  ) {
    return request<CodeIntelligenceResult>(
      "/code-intelligence/inspect",
      {
        method: "POST",
        body: JSON.stringify(
          payload,
        ),
      },
    )
  },
}
