import type {
  CodeIntelligenceRequest,
  CodeIntelligenceResult,
} from "../../core/api/code_intelligence_api"
import {
  CodeIntelligenceFeatureStore,
} from "./code_intelligence_feature_store"

export class CodeIntelligenceFeatureController {
  readonly store:
    CodeIntelligenceFeatureStore

  constructor(
    store = new CodeIntelligenceFeatureStore(),
  ) {
    this.store = store
  }

  async inspect(
    request: CodeIntelligenceRequest,
  ): Promise<CodeIntelligenceResult> {
    const normalized = this.normalize(request)
    return this.store.inspect(normalized)
  }

  clear(): void {
    this.store.clear()
  }

  dispose(): void {
    this.store.clear()
  }

  private normalize(
    request: CodeIntelligenceRequest,
  ): CodeIntelligenceRequest {
    if (!request || typeof request !== "object") {
      throw new TypeError(
        "code intelligence request required",
      )
    }

    if (
      typeof request.query !== "string"
      || !request.query.trim()
    ) {
      throw new ValueError(
        "code intelligence query required",
      )
    }

    const workspace = (
      request.workspace ?? "."
    ).trim()

    if (!workspace) {
      throw new ValueError(
        "code intelligence workspace required",
      )
    }

    const path = request.path?.trim()

    return {
      ...request,
      query: request.query.trim(),
      workspace,
      path: path || undefined,
      metadata: request.metadata
        ? { ...request.metadata }
        : undefined,
    }
  }
}

class ValueError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ValueError"
  }
}
