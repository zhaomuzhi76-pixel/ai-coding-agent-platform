import {
  describe,
  expect,
  it,
  vi,
} from "vitest"
import {
  ProjectSessionAgentWorkspaceBridge,
} from "../project_session_agent_workspace_bridge"

function projectSession() {
  const project = {
    project: {
      project_id: "p-1",
      name: "Project",
      root_path: "/tmp/p",
      workspace_id: null,
      ready: true,
    },
  }

  const session = {
    session_id: "s-1",
    project_id: "p-1",
    workspace_id: null,
    runtime_id: null,
    root_path: "/tmp/p",
    state: "active",
    status: "active",
    metadata: {},
    ready: true,
  }

  return {
    store: {
      getSnapshot: vi.fn(() => ({
        project,
        session,
      })),
    },
    selectProject: vi.fn(async () => ({
      name: "ProjectResponse",
      version: "1.0",
      ...project,
      state: "ready",
      ready: true,
    })),
    restoreActiveSession:
      vi.fn<() => Promise<typeof session | null>>(
        async () => session,
      ),
    createSession: vi.fn(async () => session),
    startSession: vi.fn(async () => session),
    closeSession: vi.fn(async () => session),
    dispose: vi.fn(),
  }
}

function workspace() {
  return {
    selectSession: vi.fn(async () => undefined),
    closeSocket: vi.fn(),
    reset: vi.fn(),
  }
}

describe(
  "ProjectSessionAgentWorkspaceBridge",
  () => {
    it(
      "restores active session on project selection",
      async () => {
        const ps = projectSession()
        const ws = workspace()

        const bridge =
          new ProjectSessionAgentWorkspaceBridge(
            ps as never,
            ws as never,
          )

        await bridge.selectProject("p-1")

        expect(
          ps.selectProject,
        ).toHaveBeenCalledWith("p-1")

        expect(
          ps.restoreActiveSession,
        ).toHaveBeenCalledWith("p-1")

        expect(
          ws.selectSession,
        ).toHaveBeenCalledWith("s-1")
      },
    )

    it(
      "creates and binds a session when no active session exists",
      async () => {
        const ps = projectSession()
        const ws = workspace()
        ps.restoreActiveSession.mockResolvedValue(
          null,
        )

        const bridge =
          new ProjectSessionAgentWorkspaceBridge(
            ps as never,
            ws as never,
          )

        await bridge.selectProject("p-1")

        expect(


          ps.createSession,


        ).toHaveBeenCalledWith({


          project_id: "p-1",


        })



        expect(


          ws.selectSession,


        ).toHaveBeenCalledWith("s-1")
      },
    )

    it(
      "cleans previous workspace before switching",
      async () => {
        const ps = projectSession()
        const ws = workspace()

        const bridge =
          new ProjectSessionAgentWorkspaceBridge(
            ps as never,
            ws as never,
          )

        await bridge.selectProject("p-1")

        expect(
          ws.reset,
        ).toHaveBeenCalledTimes(1)

        expect(
          ws.reset,
        ).toHaveBeenCalledTimes(1)
      },
    )
  },
)
