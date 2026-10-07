import {
  describe,
  expect,
  it,
} from "vitest"
import {
  ProjectSessionFeatureStore,
  type ProjectSessionFeatureGateway,
} from "../project_session_feature_store"
import type {
  ProjectResponse,
  SessionResponse,
} from "../../../core/api/api_types"

const project: ProjectResponse = {
  name: "ProjectModel",
  version: "1.1",
  project: {
    project_id: "p-1",
    name: "Demo",
    root_path: "/tmp/demo",
    workspace_id: null,
    ready: true,
  },
  state: "created",
  ready: true,
}

const session = (
  status = "created",
): SessionResponse => ({
  name: "ProjectSessionModel",
  version: "1.1",
  session_id: "s-1",
  project_id: "p-1",
  workspace_id: null,
  runtime_id: null,
  root_path: "/tmp/demo",
  state: status,
  status,
  metadata: {},
  ready: status !== "closed",
})

function gateway(): ProjectSessionFeatureGateway {
  return {
    async getProject() {
      return project
    },
    async createProject() {
      return project
    },
    async removeProject() {
      return project
    },
    async createSession() {
      return session()
    },
    async loadSession() {
      return session()
    },
    async startSession() {
      return session("active")
    },
    async closeSession() {
      return session("closed")
    },
    async removeSession() {
      return {
        session_id: "s-1",
        removed: true,
      }
    },
    projectSessions: async () => ({
      sessions: [],
      count: 0,
    }),
  }
}

describe(
  "ProjectSessionFeatureStore",
  () => {
    it("keeps project/session identity", async () => {
      const store =
        new ProjectSessionFeatureStore(
          gateway(),
        )

      await store.loadProject("p-1")
      await store.createSession({
        project_id: "p-1",
      })

      expect(
        store.getSnapshot().project?.project.project_id,
      ).toBe("p-1")

      expect(
        store.getSnapshot().session?.project_id,
      ).toBe("p-1")
    })

    it("tracks the real session lifecycle", async () => {
      const store =
        new ProjectSessionFeatureStore(
          gateway(),
        )

      await store.createSession({
        project_id: "p-1",
      })
      expect(
        store.getSnapshot().session?.status,
      ).toBe("created")

      await store.startSession("s-1")
      expect(
        store.getSnapshot().session?.status,
      ).toBe("active")

      await store.closeSession("s-1")
      expect(
        store.getSnapshot().session?.status,
      ).toBe("closed")

      await store.removeSession("s-1")
      expect(
        store.getSnapshot().session,
      ).toBeNull()
    })

    it("projects failures into stable error state", async () => {
      const failing: ProjectSessionFeatureGateway =
        {
          ...gateway(),
          async getProject() {
            throw new Error(
              "project unavailable",
            )
          },
        }

      const store =
        new ProjectSessionFeatureStore(
          failing,
        )

      await expect(
        store.loadProject("p-1"),
      ).rejects.toThrow(
        "project unavailable",
      )

      expect(
        store.getSnapshot().phase,
      ).toBe("error")

      expect(
        store.getSnapshot().error,
      ).toBe(
        "project unavailable",
      )
    })
  },
)
