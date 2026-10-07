export type AgentWorkspaceCommand =
  | {
      type: "execute"
      payload: unknown
    }
  | {
      type: "reset"
    }
  | {
      type: "connect"
    }
