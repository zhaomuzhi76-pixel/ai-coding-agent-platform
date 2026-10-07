import type {
  AgentRuntimeMessage,
} from "../../../core/contracts/execution_event"

export type ExecutionEventKind =
  | "step"
  | "result"
  | "end"
  | "error"
  | "message"
  | "unknown"

export interface ExecutionTimelineEvent {
  id: number
  kind: ExecutionEventKind
  type: string
  sessionId: string | null
  model: string | null
  data: unknown
  receivedAt: number
}

export interface ExecutionTimelineSnapshot {
  events: readonly ExecutionTimelineEvent[]
  latest: ExecutionTimelineEvent | null
  terminal: boolean
  failed: boolean
}

export class ExecutionEventTimeline {
  private readonly events:
    ExecutionTimelineEvent[] = []

  private sequence = 0

  append(
    message: AgentRuntimeMessage,
  ): ExecutionTimelineEvent {
    const event =
      this.normalize(message)

    this.events.push(event)

    return event
  }

  clear(): void {
    this.events.length = 0
    this.sequence = 0
  }

  snapshot(): ExecutionTimelineSnapshot {
    const latest =
      this.events.at(-1) ?? null

    return {
      events: [...this.events],
      latest,
      terminal:
        latest?.kind === "result"
        || latest?.kind === "end"
        || latest?.kind === "error",
      failed:
        latest?.kind === "error",
    }
  }

  count(): number {
    return this.events.length
  }

  private normalize(
    message: AgentRuntimeMessage,
  ): ExecutionTimelineEvent {
    if (message.type === "step") {
      return {
        id: ++this.sequence,
        kind: "step",
        type: message.data.type,
        sessionId: message.session_id,
        model: null,
        data: message.data,
        receivedAt: Date.now(),
      }
    }

    if (message.type === "result") {
      return {
        id: ++this.sequence,
        kind: "result",
        type: "result",
        sessionId: message.session_id,
        model: message.model ?? null,
        data: message.data,
        receivedAt: Date.now(),
      }
    }

    if (message.type === "end") {
      return {
        id: ++this.sequence,
        kind: "end",
        type: "end",
        sessionId: message.session_id,
        model: message.model ?? null,
        data: null,
        receivedAt: Date.now(),
      }
    }

    if (message.type === "token") {
      return {
        id: ++this.sequence,
        kind: "message",
        type: "token",
        sessionId: message.session_id,
        model: null,
        data: message.content,
        receivedAt: Date.now(),
      }
    }

    return {
      id: ++this.sequence,
      kind: "error",
      type: "error",
      sessionId: message.session_id,
      model: null,
      data: message.data,
      receivedAt: Date.now(),
    }
  }
}
