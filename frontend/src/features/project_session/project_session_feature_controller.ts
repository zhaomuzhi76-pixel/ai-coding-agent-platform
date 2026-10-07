import type {
  CreateSessionPayload,
} from "../../core/api/project_session_api"
import {
  ProjectSessionFeatureStore,
} from "./project_session_feature_store"

export class ProjectSessionFeatureController {
  readonly store:
    ProjectSessionFeatureStore

  constructor(
    store = new ProjectSessionFeatureStore(),
  ) {
    this.store = store
  }

  async selectProject(
    projectId: string,
  ) {
    return this.store.loadProject(
      this.requireId(
        projectId,
        "project id",
      ),
    )
  }

  async restoreActiveSession(
    projectId: string,
  ) {
    return this.store.findActiveSession(
      this.requireId(
        projectId,
        "project id",
      ),
    )
  }

  async createProject(
    payload: {
      name: string
      root_path: string
      project_id?: string
      workspace_id?: string
    },
  ) {
    return this.store.createProject({
      name: payload.name,
      rootPath: payload.root_path,
      projectId: payload.project_id,
      workspaceId: payload.workspace_id,
    })
  }

  async createSession(
    payload: CreateSessionPayload,
  ) {
    return this.store.createSession(payload)
  }

  async startSession(
    sessionId: string,
  ) {
    return this.store.startSession(
      this.requireId(
        sessionId,
        "session id",
      ),
    )
  }

  async closeSession(
    sessionId: string,
  ) {
    return this.store.closeSession(
      this.requireId(
        sessionId,
        "session id",
      ),
    )
  }

  async removeSession(
    sessionId: string,
  ) {
    return this.store.removeSession(
      this.requireId(
        sessionId,
        "session id",
      ),
    )
  }

  dispose(): void {
    this.store.clear()
  }

  private requireId(
    value: string,
    label: string,
  ): string {
    if (
      typeof value !== "string"
      || !value.trim()
    ) {
      throw new Error(
        `${label} required`,
      )
    }
    return value.trim()
  }
}
