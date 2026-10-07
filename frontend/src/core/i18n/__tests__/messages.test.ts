import { describe, expect, it } from "vitest"

import { message } from "../messages"
import { CORE } from "../messages_core"
import { PAGES } from "../messages_pages"

describe("i18n messages", () => {
  it("core keys aligned across zh-CN and en-US", () => {
    const zh = Object.keys(CORE["zh-CN"]).sort()
    const en = Object.keys(CORE["en-US"]).sort()
    expect(en).toEqual(zh)
  })

  it("page keys aligned across zh-CN and en-US", () => {
    const zh = Object.keys(PAGES["zh-CN"]).sort()
    const en = Object.keys(PAGES["en-US"]).sort()
    expect(en).toEqual(zh)
  })

  it("returns zh-CN translation for zh locale", () => {
    expect(message("zh-CN", "app.name")).toBe("编程 AI Agent")
    expect(message("zh-CN", "nav.platform")).toBe("平台")
  })

  it("returns en-US translation for en locale", () => {
    expect(message("en-US", "app.name")).toBe("Biancheng AI Agent")
    expect(message("en-US", "nav.platform")).toBe("Platform")
  })

  it("falls back to key when unknown", () => {
    // @ts-expect-error deliberately bad key
    expect(message("zh-CN", "totally.missing.key")).toBe("totally.missing.key")
  })

  it("returns non-empty for all nav keys", () => {
    const navKeys = [
      "nav.coding", "nav.platform", "nav.models",
      "nav.finetune", "nav.mcp", "nav.security", "nav.monitor",
    ] as const
    for (const k of navKeys) {
      expect(message("zh-CN", k).length).toBeGreaterThan(0)
      expect(message("en-US", k).length).toBeGreaterThan(0)
    }
  })
})
