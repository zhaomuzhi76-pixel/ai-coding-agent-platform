import {
  describe,
  expect,
  it,
} from "vitest"
import type {
  CodeIntelligenceRequest,
  CodeIntelligenceResult,
} from "../../../core/api/code_intelligence_api"
import type {
  CodeIntelligenceFeatureGateway,
} from "../code_intelligence_feature_gateway"
import {
  CodeIntelligenceFeatureController,
} from "../code_intelligence_feature_controller"
import {
  CodeIntelligenceFeatureStore,
} from "../code_intelligence_feature_store"

const result: CodeIntelligenceResult = {
  name: "CodeIntelligenceResult",
  findings: [{ workspace: "/workspace/project", files: 3 }],
  metadata: { operation: "summary" },
  ready: true,
}

function gateway(
  inspect: (
    request: CodeIntelligenceRequest,
  ) => Promise<CodeIntelligenceResult>,
): CodeIntelligenceFeatureGateway {
  return { inspect }
}

describe("code intelligence feature", () => {
  it("executes a normalized request", async () => {
    const calls: CodeIntelligenceRequest[] = []
    const store = new CodeIntelligenceFeatureStore(
      gateway(async request => {
        calls.push(request)
        return result
      }),
    )

    const value =
      await new CodeIntelligenceFeatureController(store).inspect({
        query: " inspect project ",
        workspace: " /workspace/project ",
        metadata: { operation: "summary" },
      })

    expect(value).toBe(result)
    expect(calls).toHaveLength(1)
    expect(calls[0]).toEqual({
      query: "inspect project",
      workspace: "/workspace/project",
      path: undefined,
      metadata: { operation: "summary" },
    })
    expect(store.getSnapshot().phase).toBe("ready")
    expect(store.getSnapshot().result).toBe(result)
    expect(store.getSnapshot().revision).toBe(1)
  })

  it("preserves failure state", async () => {
    const error = new Error("inspection failed")
    const store = new CodeIntelligenceFeatureStore(
      gateway(async () => {
        throw error
      }),
    )

    await expect(
      store.inspect({ query: "inspect" }),
    ).rejects.toBe(error)

    const state = store.getSnapshot()
    expect(state.phase).toBe("error")
    expect(state.error).toBe("inspection failed")
    expect(state.revision).toBe(1)
  })

  it("rejects an invalid gateway result", async () => {
    const store = new CodeIntelligenceFeatureStore(
      gateway(async () => ({
        ...result,
        ready: false,
      })),
    )

    await expect(
      store.inspect({ query: "inspect" }),
    ).rejects.toThrow("invalid result")

    expect(store.getSnapshot().phase).toBe("error")
  })

  it("prevents stale results from overwriting newer state", async () => {
    let releaseFirst: (
      value: CodeIntelligenceResult,
    ) => void = () => undefined

    const first = new Promise<CodeIntelligenceResult>(
      resolve => {
        releaseFirst = resolve
      },
    )

    const secondResult: CodeIntelligenceResult = {
      ...result,
      findings: [{ workspace: "/workspace/project", files: 99 }],
      metadata: { operation: "project" },
    }

    let calls = 0
    const store = new CodeIntelligenceFeatureStore(
      gateway(async () => {
        calls += 1
        return calls === 1 ? first : secondResult
      }),
    )

    const firstRequest = store.inspect({
      query: "first",
    })
    const secondRequest = store.inspect({
      query: "second",
      metadata: { operation: "project" },
    })

    await secondRequest
    expect(store.getSnapshot().request?.query).toBe("second")
    expect(store.getSnapshot().result).toBe(secondResult)
    expect(store.getSnapshot().revision).toBe(2)

    releaseFirst(result)
    await firstRequest

    const state = store.getSnapshot()
    expect(state.request?.query).toBe("second")
    expect(state.result).toBe(secondResult)
    expect(state.phase).toBe("ready")
    expect(state.revision).toBe(2)
  })

  it("clears state monotonically", async () => {
    const store = new CodeIntelligenceFeatureStore(
      gateway(async () => result),
    )

    await store.inspect({ query: "inspect" })
    const before = store.getSnapshot().revision
    store.clear()

    const state = store.getSnapshot()
    expect(state.phase).toBe("idle")
    expect(state.request).toBeNull()
    expect(state.result).toBeNull()
    expect(state.error).toBeNull()
    expect(state.revision).toBe(before + 1)
  })

  it("rejects invalid controller requests before transport", async () => {
    let calls = 0
    const store = new CodeIntelligenceFeatureStore(
      gateway(async () => {
        calls += 1
        return result
      }),
    )
    const controller =
      new CodeIntelligenceFeatureController(store)

    await expect(
      controller.inspect({ query: "   " }),
    ).rejects.toThrow("code intelligence query required")

    await expect(
      controller.inspect({
        query: "inspect",
        workspace: "   ",
      }),
    ).rejects.toThrow(
      "code intelligence workspace required",
    )

    expect(calls).toBe(0)
  })

  it("clears through controller disposal", () => {
    const store = new CodeIntelligenceFeatureStore(
      gateway(async () => result),
    )
    const controller =
      new CodeIntelligenceFeatureController(store)

    controller.clear()
    controller.dispose()

    expect(store.getSnapshot().phase).toBe("idle")
    expect(store.getSnapshot().result).toBeNull()
  })
})
