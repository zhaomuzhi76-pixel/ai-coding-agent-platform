import type {
  CodeIntelligenceRequest,
  CodeIntelligenceResult,
} from "../../core/api/code_intelligence_api"
import {
  Store,
} from "../../core/state/store"
import type {
  CodeIntelligenceFeatureGateway,
} from "./code_intelligence_feature_gateway"
import {
  defaultCodeIntelligenceGateway,
} from "./code_intelligence_feature_gateway"
import {
  initialCodeIntelligenceFeatureState,
  type CodeIntelligenceFeatureState,
} from "./code_intelligence_feature_state"

export type {
  CodeIntelligenceFeatureGateway,
} from "./code_intelligence_feature_gateway"

export class CodeIntelligenceFeatureStore
  extends Store<CodeIntelligenceFeatureState> {
  private readonly gateway:
    CodeIntelligenceFeatureGateway

  constructor(
    gateway: CodeIntelligenceFeatureGateway =
      defaultCodeIntelligenceGateway,
  ) {
    super(initialCodeIntelligenceFeatureState)
    this.gateway = gateway
  }

  async inspect(
    request: CodeIntelligenceRequest,
  ): Promise<CodeIntelligenceResult> {
    return this.run(request, async () => {
      const result = await this.gateway.inspect(request)

      if (
        !result
        || !Array.isArray(result.findings)
        || typeof result.metadata !== "object"
        || result.metadata === null
        || result.ready !== true
      ) {
        throw new TypeError(
          "code intelligence gateway returned invalid result",
        )
      }

      return result
    })
  }

  clear(): void {
    this.setSnapshot({
      ...initialCodeIntelligenceFeatureState,
      revision: this.getSnapshot().revision + 1,
    })
  }

  private async run<T>(
    request: CodeIntelligenceRequest,
    operation: () => Promise<T>,
  ): Promise<T> {
    const revision =
      this.getSnapshot().revision + 1

    this.update(state => ({
      ...state,
      phase: "loading",
      request,
      result: null,
      error: null,
      revision,
    }))

    try {
      const value = await operation()

      if (
        this.getSnapshot().revision
        !== revision
      ) {
        return value
      }

      this.update(state => ({
        ...state,
        phase: "ready",
        request,
        result: value as CodeIntelligenceResult,
        error: null,
      }))

      return value
    } catch (error) {
      if (
        this.getSnapshot().revision
        !== revision
      ) {
        throw error
      }

      const message =
        error instanceof Error
          ? error.message
          : "code intelligence operation failed"

      this.update(state => ({
        ...state,
        phase: "error",
        request,
        result: null,
        error: message,
        revision,
      }))

      throw error
    }
  }
}
