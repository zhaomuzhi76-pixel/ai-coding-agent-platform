import {
  projectSessionApi,
  type CreateSessionPayload,
} from "../api/project_session_api"
import type {
  RemoveResponse,
  SessionResponse,
} from "../api/api_types"
import {
  requireSessionId,
} from "../contracts/session"
import {
  Store,
} from "../state/store"
import type {
  ProjectSessionState,
} from "./session_state"

export interface ProjectSessionGateway {
  create(
    payload: CreateSessionPayload,
  ): Promise<SessionResponse>
  get(sessionId: string): Promise<SessionResponse>
  start(sessionId: string): Promise<SessionResponse>
  close(sessionId: string): Promise<SessionResponse>
  remove(sessionId: string): Promise<RemoveResponse>
}

const gateway: ProjectSessionGateway =
  projectSessionApi

const initialState: ProjectSessionState = {
  phase: "idle",
  session: null,
  error: null,
  requestId: 0,
}

export class ProjectSessionStore
  extends Store<ProjectSessionState> {
  private readonly api: ProjectSessionGateway

  constructor(
    api: ProjectSessionGateway = gateway,
  ) {
    super(initialState)
    this.api = api
  }

  async create(
    payload: CreateSessionPayload,
  ): Promise<SessionResponse> {
    return this.run(
      "loading",
      async () => {
        const session =
          await this.api.create(payload)

        this.setSession(
          session,
          session.status === "active"
            ? "active"
            : "ready",
        )
        return session
      },
    )
  }

  async load(
    sessionId: string,
  ): Promise<SessionResponse> {
    const id = requireSessionId(sessionId)

    return this.run(
      "loading",
      async () => {
        const session =
          await this.api.get(id)

        this.setSession(
          session,
          this.phaseFor(session),
        )
        return session
      },
    )
  }

  async start(
    sessionId: string,
  ): Promise<SessionResponse> {
    const id = requireSessionId(sessionId)

    return this.run(
      "starting",
      async () => {
        const session =
          await this.api.start(id)

        this.setSession(
          session,
          "active",
        )
        return session
      },
    )
  }

  async close(
    sessionId: string,
  ): Promise<SessionResponse> {
    const id = requireSessionId(sessionId)

    return this.run(
      "closing",
      async () => {
        const session =
          await this.api.close(id)

        this.setSession(
          session,
          "closed",
        )
        return session
      },
    )
  }

  async remove(
    sessionId: string,
  ): Promise<RemoveResponse> {
    const id = requireSessionId(sessionId)

    return this.run(
      "removing",
      async () => {
        const result =
          await this.api.remove(id)

        if (result.removed) {
          this.update(state => ({
            ...state,
            phase: "removed",
            session: null,
            error: null,
          }))
        }

        return result
      },
    )
  }

  reset(): void {
    this.setSnapshot(initialState)
  }

  private async run<T>(
    phase: ProjectSessionState["phase"],
    operation: () => Promise<T>,
  ): Promise<T> {
    const requestId =
      this.getSnapshot().requestId + 1

    this.update(state => ({
      ...state,
      phase,
      error: null,
      requestId,
    }))

    try {
      return await operation()
    } catch (error) {
      this.update(state => ({
        ...state,
        phase: "error",
        error: {
          message:
            error instanceof Error
              ? error.message
              : "session operation failed",
        },
      }))
      throw error
    }
  }

  private setSession(
    session: SessionResponse,
    phase: ProjectSessionState["phase"],
  ): void {
    this.update(state => ({
      ...state,
      phase,
      session,
      error: null,
    }))
  }

  private phaseFor(
    session: SessionResponse,
  ): ProjectSessionState["phase"] {
    if (session.status === "active") {
      return "active"
    }

    if (session.status === "closed") {
      return "closed"
    }

    return "ready"
  }
}
