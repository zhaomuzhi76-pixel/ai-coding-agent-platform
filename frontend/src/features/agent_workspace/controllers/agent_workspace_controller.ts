import type {
  AgentWorkspaceStore,
} from "../agent_workspace_store"

export class AgentWorkspaceController {
  private readonly store: AgentWorkspaceStore

  constructor(store: AgentWorkspaceStore) {
    this.store = store
  }

  async execute() {
    return this.store.execute()
  }

  async selectSession(sessionId: string) {
    return this.store.selectSession(sessionId)
  }

  setMessage(message: string) {
    this.store.setMessage(message)
  }

  setModelSelection(
    model: Parameters<
      AgentWorkspaceStore["setModelSelection"]
    >[0],
  ) {
    this.store.setModelSelection(model)
  }

  clearResult() {
    this.store.clearResult()
  }

  dispose() {
    this.store.dispose()
  }
}
