import { beforeEach, describe, expect, it, vi } from "vitest"

import { PlatformStore } from "../platform_store"
import type { PlatformGateway } from "../platform_gateway"
import type {
  PlatformModelOption,
  PlatformProposal,
} from "../../../core/contracts/platform"

function modelOption(name: string): PlatformModelOption {
  return {
    model: name,
    provider: "test",
    display_name: name,
    context_window: 32000,
    supports_tool_call: true,
    supports_stream: true,
    supports_embedding: false,
    cost_input_per_1k: 0,
    cost_output_per_1k: 0,
    strengths: [],
  }
}

function proposal(
  id: string,
  status: PlatformProposal["status"],
): PlatformProposal {
  return {
    proposal_id: id,
    task: "t",
    plan: "p",
    changes: [{ file: "a.py", kind: "prepend", text: "x\n" }],
    attempts: 1,
    status,
    file_count: 1,
    created_at: 0,
    updated_at: 0,
    error: "",
  }
}

function gateway(): PlatformGateway {
  return {
    createSession: vi.fn().mockResolvedValue({
      session_id: "s1", workspace: "/ws", user_id: "u",
      locale: "zh-CN", model: "qwen-max",
    }),
    propose: vi.fn().mockResolvedValue(proposal("p1", "pending")),
    approve: vi.fn().mockResolvedValue(proposal("p1", "approved")),
    reject: vi.fn().mockResolvedValue(proposal("p1", "rejected")),
    apply: vi.fn().mockResolvedValue({
      proposal: proposal("p1", "applied"),
      result: { ok: true },
    }),
    verify: vi.fn().mockResolvedValue({
      proposal: proposal("p1", "applied"),
      result: { ok: true },
    }),
    learn: vi.fn().mockResolvedValue({
      proposal_id: "p1", learned: true,
    }),
    listModels: vi.fn().mockResolvedValue([modelOption("m1")]),
    listDomains: vi.fn().mockResolvedValue([
      { name: "agriculture", entity_types: ["crop"], terms: 2 },
    ]),
  }
}

describe("PlatformStore", () => {
  let g: PlatformGateway
  let store: PlatformStore

  beforeEach(() => {
    g = gateway()
    store = new PlatformStore(g)
  })

  it("loads catalog on init", async () => {
    await store.loadCatalog()
    const s = store.getSnapshot()
    expect(s.phase).toBe("ready")
    expect(s.models).toHaveLength(1)
    expect(s.domains).toHaveLength(1)
    expect(s.selectedModel).toBe("m1")
    expect(s.selectedDomain).toBe("agriculture")
  })

  it("creates session and clears proposals", async () => {
    await store.loadCatalog()
    await store.startSession({
      workspace: "/ws", userId: "u", locale: "zh-CN",
    })
    const s = store.getSnapshot()
    expect(s.session?.session_id).toBe("s1")
    expect(s.proposals).toHaveLength(0)
    expect(s.stageCursor).toBe(0)
  })

  it("propose advances stageCursor to 1", async () => {
    await store.loadCatalog()
    await store.startSession({
      workspace: "/ws", userId: "u", locale: "zh-CN",
    })
    await store.propose({ task: "add", files: ["a.py"] })
    const s = store.getSnapshot()
    expect(s.proposals).toHaveLength(1)
    expect(s.activeProposalId).toBe("p1")
    expect(s.stageCursor).toBe(1)
  })

  it("approve/apply/verify/learn advance stage", async () => {
    await store.loadCatalog()
    await store.startSession({
      workspace: "/ws", userId: "u", locale: "zh-CN",
    })
    await store.propose({ task: "add", files: ["a.py"] })

    await store.approve()
    expect(store.getSnapshot().stageCursor).toBe(2)

    await store.apply()
    expect(store.getSnapshot().stageCursor).toBe(3)

    await store.verify()
    expect(store.getSnapshot().stageCursor).toBe(4)

    await store.learn()
    expect(store.getSnapshot().stageCursor).toBe(5)
  })

  it("reject resets stageCursor", async () => {
    await store.loadCatalog()
    await store.startSession({
      workspace: "/ws", userId: "u", locale: "zh-CN",
    })
    await store.propose({ task: "add", files: ["a.py"] })
    await store.reject("no")
    const s = store.getSnapshot()
    expect(s.proposals[0].status).toBe("rejected")
    expect(s.stageCursor).toBe(0)
  })

  it("errors without session", async () => {
    await store.loadCatalog()
    await expect(
      store.propose({ task: "x", files: ["a.py"] }),
    ).rejects.toThrow("no session")
  })

  it("emits to subscribers", async () => {
    const listener = vi.fn()
    store.subscribe(listener)
    await store.loadCatalog()
    expect(listener).toHaveBeenCalled()
  })

  it("error phase on catalog failure", async () => {
    g.listModels = vi.fn().mockRejectedValue(new Error("boom"))
    store = new PlatformStore(g)
    await store.loadCatalog()
    expect(store.getSnapshot().phase).toBe("error")
    expect(store.getSnapshot().error).toContain("boom")
  })
})
