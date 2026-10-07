import { describe, it, expect } from "vitest"
import {
  diffWorkspace, applyWorkspace,
  serializePatches, deserializePatches,
} from "../workspace_persist_patch"
import type { PersistedWorkspace } from "../workspace_persistence_contract"

function W(overrides: Partial<PersistedWorkspace> = {}): PersistedWorkspace {
  return {
    version: 1,
    boundary: {
      projectId: "prj-x",
      workspace: "/tmp/x",
      targetPath: ".",
      targetKind: "directory",
    },
    name: "x",
    kind: "directory",
    activeFile: null,
    expanded: ["a", "b"],
    ...overrides,
  }
}

describe("diffWorkspace", () => {
  it("无变化 → 空 patch", () => {
    expect(diffWorkspace(W(), W())).toEqual([])
  })
  it("activeFile 变 → 1 个 patch", () => {
    const p = diffWorkspace(W(), W({ activeFile: "a.py" }))
    expect(p).toHaveLength(1)
    expect(p[0].path).toBe("/activeFile")
    expect(p[0].value).toBe("a.py")
  })
  it("expanded 变 → 整数组 replace", () => {
    const p = diffWorkspace(W(), W({ expanded: ["a", "c"] }))
    expect(p).toHaveLength(1)
    expect(p[0].path).toBe("/expanded")
    expect(p[0].value).toEqual(["a", "c"])
  })
  it("多字段变 → 多个 patch", () => {
    const p = diffWorkspace(W(), W({ activeFile: "a.py", kind: "file" }))
    expect(p.map(x => x.path).sort()).toEqual(["/activeFile", "/kind"])
  })
})

describe("applyWorkspace", () => {
  it("空 patches → 深拷贝 base", () => {
    const base = W()
    const r = applyWorkspace(base, [])
    expect(r).toEqual(base)
    expect(r).not.toBe(base)
  })
  it("单 patch", () => {
    const r = applyWorkspace(W(), [{ op: "replace", path: "/activeFile", value: "x" }])
    expect(r.activeFile).toBe("x")
  })
  it("多 patch", () => {
    const r = applyWorkspace(W(), [
      { op: "replace", path: "/activeFile", value: "x" },
      { op: "replace", path: "/kind", value: "file" },
    ])
    expect(r.activeFile).toBe("x")
    expect(r.kind).toBe("file")
  })
  it("白名单外 path 被忽略", () => {
    const r = applyWorkspace(W(), [
      { op: "replace", path: "/__proto__", value: { hacked: true } },
    ])
    expect((r as Record<string, unknown>).__proto__).toBeDefined()
    expect((r as Record<string, unknown>).hacked).toBeUndefined()
  })
})

describe("round-trip", () => {
  it("base + diff → 应用 → 恢复", () => {
    const a = W()
    const b = W({ activeFile: "z.py", kind: "file", expanded: ["x", "y", "z"] })
    const patches = diffWorkspace(a, b)
    const restored = applyWorkspace(a, patches)
    expect(restored).toEqual(b)
  })
  it("多次链式 patch", () => {
    const s0 = W()
    const s1 = W({ activeFile: "a.py" })
    const s2 = W({ activeFile: "b.py", expanded: ["x"] })
    const p1 = diffWorkspace(s0, s1)
    const p2 = diffWorkspace(s1, s2)
    const merged = [...p1, ...p2]
    const r = applyWorkspace(s0, merged)
    expect(r).toEqual(s2)
  })
})

describe("serialize/deserialize", () => {
  it("往返", () => {
    const patches = diffWorkspace(W(), W({ activeFile: "x" }))
    const json = serializePatches(patches)
    expect(deserializePatches(json)).toEqual(patches)
  })
  it("null 安全", () => {
    expect(deserializePatches(null)).toEqual([])
  })
  it("非法 JSON 返回空数组", () => {
    expect(deserializePatches("{bad}")).toEqual([])
  })
  it("过滤非法项", () => {
    const bad = JSON.stringify([{ op: "add", path: "/x", value: 1 }, { op: "replace", path: "/y", value: 2 }])
    expect(deserializePatches(bad)).toEqual([{ op: "replace", path: "/y", value: 2 }])
  })
})
