import { beforeEach, describe, expect, it, vi } from "vitest"

import { platformApi } from "../platform_api"

function jsonResponse(body: unknown, status = 200) {
  return new Response(
    JSON.stringify(body),
    { status, headers: { "Content-Type": "application/json" } },
  )
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe("platformApi", () => {
  it("listModels unwraps ok envelope", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jsonResponse({
        ok: true,
        data: { models: [{ model: "m1" }] },
      }),
    ))
    const r = await platformApi.listModels()
    expect(r.models).toHaveLength(1)
    expect(r.models[0].model).toBe("m1")
  })

  it("throws on ok=false envelope (status 200)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jsonResponse({
        ok: false,
        error: { code: "BAD_REQUEST", message: "x" },
      }, 200),
    ))
    await expect(platformApi.listModels()).rejects.toThrow(/BAD_REQUEST/)
  })

  it("throws on HTTP error status", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jsonResponse({ ok: false }, 400),
    ))
    await expect(platformApi.listModels()).rejects.toThrow(/400/)
  })

  it("createSession posts correct payload", async () => {
    const spy = vi.fn().mockResolvedValue(
      jsonResponse({
        ok: true,
        data: { session_id: "s1", workspace: "/w",
                user_id: "u", locale: "zh-CN", model: "m" },
      }),
    )
    vi.stubGlobal("fetch", spy)
    const r = await platformApi.createSession({
      workspace: "/w", user_id: "u", model: "m",
    })
    expect(r.session_id).toBe("s1")
    const [, init] = spy.mock.calls[0]
    expect(init.method).toBe("POST")
    const body = JSON.parse(init.body as string)
    expect(body.workspace).toBe("/w")
    expect(body.model).toBe("m")
  })

  it("listDomains unwraps domains", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      jsonResponse({
        ok: true,
        data: { domains: [
          { name: "agriculture", entity_types: ["crop"], terms: 2 },
        ] },
      }),
    ))
    const r = await platformApi.listDomains()
    expect(r.domains).toHaveLength(1)
    expect(r.domains[0].name).toBe("agriculture")
  })
})
