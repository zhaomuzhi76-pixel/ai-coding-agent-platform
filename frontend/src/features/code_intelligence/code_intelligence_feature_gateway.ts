import {
  codeIntelligenceApi,
  type CodeIntelligenceRequest,
} from "../../core/api/code_intelligence_api"
import type {
  CodeIntelligenceResult,
} from "../../core/api/code_intelligence_api"

export interface CodeIntelligenceFeatureGateway {
  inspect(
    payload: CodeIntelligenceRequest,
  ): Promise<CodeIntelligenceResult>
}

export const defaultCodeIntelligenceGateway:
  CodeIntelligenceFeatureGateway = {
  inspect: codeIntelligenceApi.inspect,
}
