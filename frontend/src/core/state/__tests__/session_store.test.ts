import {
  describe,
  expect,
  it,
} from "vitest"
import {
  ProjectSessionStore,
  type ProjectSessionGateway,
} from "../../session/project_session_store"
import type {
  SessionResponse,
} from "../../api/api_types"

function session(
  status: string,
): SessionResponse {
  return {
    name: "session",
    version: "1.0",
    session_id: "s-1",
    project_id: "p-1",
    workspace_id: null,
    runtime_id: null,
    root_path: "/tmp/project",
    state: status,
    status,
    metadata: {},
    ready: true,
  }
}

function gateway(): ProjectSessionGateway {
  let current = session("ready")

  return {
    async create() {
      current = session("ready")
      return current
    },
    async get() {
      return current
    },
    async start() {
      current = session("active")
      return current
    },
    async close() {
      current = session("closed")
      return current
    },
    async remove() {
      return {
        session_id: "s-1",
        removed: true,
      }
    },
  }
}

describe("ProjectSessionStore", () => {
  it(
    "transitions create -> ready -> active -> closed -> removed",
    async () => {
      const store =
        new ProjectSessionStore(gateway())

      await store.create({
        project_id: "p-1",
      })
      expect(
        store.getSnapshot().phase,
      ).toBe("ready")

      await store.start("s-1")
      expect(
        store.getSnapshot().phase,
      ).toBe("active")

      await store.close("s-1")
      expect(
        store.getSnapshot().phase,
      ).toBe("closed")

      await store.remove("s-1")
      expect(
        store.getSnapshot().phase,
      ).toBe("removed")
      expect(
        store.getSnapshot().session,
      ).toBeNull()
    },
  )

  it(
    "rejects invalid session identifiers",
    async () => {
      const store =
        new ProjectSessionStore(gateway())

      await expect(
        store.start(""),
      ).rejects.toThrow("session id required")
    },
  )

  it("notifies subscribers and cleans them up", async () => {
    const store =
      new ProjectSessionStore(gateway())
    let calls = 0

    const unsubscribe =
      store.subscribe(() => {
        calls += 1
      })

    await store.create({
      project_id: "p-1",
    })

    unsubscribe()

    await store.start("s-1")

    expect(calls).toBe(2)
  })
})
