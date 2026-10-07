import {
  describe,
  expect,
  it,
  vi,
} from "vitest"

import {
  AgentWorkspaceStore,
} from "../agent_workspace_store"

import {
  AgentWorkspaceController,
} from "../controllers/agent_workspace_controller"

function gateway() {
  return {
    loadSession: vi.fn()
      .mockResolvedValue({
        session_id: "s1",
        root_path: "/tmp",
        project_id: "p1",
        status: "active",
        ready: true,
      }),

    createSocket: vi.fn()
      .mockReturnValue({
        connect: vi.fn(),
        close: vi.fn(),
        execute: vi.fn()
          .mockResolvedValue({
            success: true,
          }),
      }),
  }
}

describe(
  "AgentWorkspaceStore",
  () => {
    it(
      "loads an active session and executes through controller",
      async () => {
        const store =
          new AgentWorkspaceStore(
            gateway(),
          )

        const controller =
          new AgentWorkspaceController(
            store,
          )

        await store.selectSession(
          "s1",
        )

        controller.setMessage(
          "inspect the project",
        )

        const result =
          await controller.execute()

        expect(
          result.success,
        ).toBe(true)
      },
    )

    it(
      "rejects execution without required context",
      async () => {
        const store =
          new AgentWorkspaceStore(
            gateway(),
          )

        const controller =
          new AgentWorkspaceController(
            store,
          )

        await expect(
          controller.execute(),
        ).rejects.toThrow(
          "agent session required",
        )
      },
    )

    it(
      "rejects execution without a message",
      async () => {
        const store =
          new AgentWorkspaceStore(
            gateway(),
          )

        const controller =
          new AgentWorkspaceController(
            store,
          )

        await store.selectSession(
          "s1",
        )

        await expect(
          controller.execute(),
        ).rejects.toThrow(
          "agent message required",
        )
      },
    )

    it(
      "clears the previous message when selecting a session",
      async () => {
        const store =
          new AgentWorkspaceStore(
            gateway(),
          )

        controllerSetMessage(
          store,
          "previous project request",
        )

        await store.selectSession(
          "s1",
        )

        expect(
          store.getSnapshot().message,
        ).toBe("")
      },
    )

    it(
      "accepts websocket events",
      () => {
        const store =
          new AgentWorkspaceStore(
            gateway(),
          )

        store.appendMessage({
          type: "token",
          session_id: "session-1",
          content: "hello",
        })

        expect(
          store.getSnapshot()
            .messages.length,
        ).toBe(1)
      },
    )
  },
)

function controllerSetMessage(
  store: AgentWorkspaceStore,
  message: string,
) {
  store.setMessage(message)
}
