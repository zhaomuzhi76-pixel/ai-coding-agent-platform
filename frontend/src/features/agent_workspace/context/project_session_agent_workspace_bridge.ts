import type {
  ProjectSessionFeatureController,
} from "../../project_session/project_session_feature_controller"

import type {
  AgentWorkspaceStore,
} from "../agent_workspace_store"

export interface AgentWorkspaceContextBridge {
  selectProject(
    projectId: string,
  ): Promise<void>

  createSession(): Promise<void>

  startSession(): Promise<void>

  closeSession(): Promise<void>

  clear(): void

  ready(): boolean
}

export class ProjectSessionAgentWorkspaceBridge
  implements AgentWorkspaceContextBridge {
  private readonly projectSession:
    ProjectSessionFeatureController

  private readonly workspace:
    AgentWorkspaceStore

  constructor(
    projectSession: ProjectSessionFeatureController,
    workspace: AgentWorkspaceStore,
  ) {
    this.projectSession = projectSession
    this.workspace = workspace
  }

  async selectProject(
    projectId: string,
  ): Promise<void> {
    this.workspace.reset()

    const project =
      await this.projectSession.selectProject(
        projectId,
      )

    if (!project.project.ready) {
      throw new Error(
        "project is not ready",
      )
    }

    const active =
      await this.projectSession.restoreActiveSession(
        project.project.project_id,
      )

    if (
      active?.status === "active"
      && active.ready
    ) {
      await this.workspace.selectSession(
        active.session_id,
      )
      return
    }

    const created =
      await this.projectSession.createSession({
        project_id:
          project.project.project_id,
      })

    const started =
      await this.projectSession.startSession(
        created.session_id,
      )

    if (
      started.status !== "active"
      || !started.ready
    ) {
      throw new Error(
        "project session failed to start",
      )
    }

    await this.workspace.selectSession(
      started.session_id,
    )
  }

  async createSession(): Promise<void> {
    const project =
      this.projectSession.store
        .getSnapshot()
        .project?.project

    if (!project) {
      throw new Error(
        "project required",
      )
    }

    const session =
      await this.projectSession.createSession({
        project_id:
          project.project_id,
      })

    await this.workspace.selectSession(
      session.session_id,
    )
  }

  async startSession(): Promise<void> {
    const session =
      this.requireSession()

    const result =
      await this.projectSession.startSession(
        session.session_id,
      )

    await this.workspace.selectSession(
      result.session_id,
    )
  }

  async closeSession(): Promise<void> {
    const session =
      this.requireSession()

    await this.projectSession.closeSession(
      session.session_id,
    )

    this.workspace.reset()
  }

  clear(): void {
    this.workspace.reset()
    this.projectSession.dispose()
  }

  ready(): boolean {
    return (
      this.projectSession.store
        .getSnapshot()
        .project
        ?.project
        .ready === true
    )
  }

  private requireSession() {
    const session =
      this.projectSession.store
        .getSnapshot()
        .session

    if (!session) {
      throw new Error(
        "session required",
      )
    }

    return session
  }
}
