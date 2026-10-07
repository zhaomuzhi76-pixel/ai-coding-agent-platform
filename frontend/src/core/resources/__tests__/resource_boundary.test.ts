import { describe, expect, it } from "vitest"
import {
  createResourceBoundary,
  normalizeTargetPath,
  resourcePath,
} from "../resource_boundary"

describe("resource boundary", () => {
  it("normalizes a relative file boundary", () => {
    const boundary = createResourceBoundary({
      projectId: "p-1",
      workspace: "/workspace/project",
      targetPath: "src\\main.tsx",
      targetKind: "file",
    })

    expect(boundary.targetPath).toBe(
      "src/main.tsx",
    )
    expect(resourcePath(boundary)).toBe(
      "/workspace/project/src/main.tsx",
    )
  })

  it("represents a folder boundary at workspace root", () => {
    const boundary = createResourceBoundary({
      projectId: null,
      workspace: "/workspace/project",
      targetPath: ".",
      targetKind: "directory",
    })

    expect(boundary.targetPath).toBe(".")
    expect(resourcePath(boundary)).toBe(
      "/workspace/project",
    )
  })

  it("rejects paths that escape workspace", () => {
    expect(() =>
      normalizeTargetPath(
        "../outside/project.ts",
      ),
    ).toThrow()
  })
})
