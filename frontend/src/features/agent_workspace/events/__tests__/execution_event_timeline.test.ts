import {
  describe,
  expect,
  it,
} from "vitest"
import {
  ExecutionEventTimeline,
} from "../execution_event_timeline"

const step = {
  schema: "runtime.event.v2" as const,
  event_id: "e-1",
  type: "node_start" as const,
  node_id: "n-1",
  data: {
    node_id: "n-1",
    executor_type: "llm",
  },
  metadata: {},
  source: "runtime.node_execution",
  timestamp: "2026-09-16T00:00:00Z",
  version: "2.1",
  responsibility: [
    "runtime_event_entity",
  ],
}

describe(
  "ExecutionEventTimeline",
  () => {
    it(
      "projects step and result events",
      () => {
        const timeline =
          new ExecutionEventTimeline()

        timeline.append({
          type: "step",
          session_id: "s-1",
          data: step,
        })

        timeline.append({
          type: "result",
          session_id: "s-1",
          model: "test-model",
          data: {
            success: true,
          },
        })

        const snapshot =
          timeline.snapshot()

        expect(
          snapshot.events,
        ).toHaveLength(2)

        expect(
          snapshot.events[0].kind,
        ).toBe("step")

        expect(
          snapshot.events[1].kind,
        ).toBe("result")

        expect(
          snapshot.terminal,
        ).toBe(true)

        expect(
          snapshot.failed,
        ).toBe(false)
      },
    )

    it(
      "preserves failure as terminal state",
      () => {
        const timeline =
          new ExecutionEventTimeline()

        timeline.append({
          type: "error",
          session_id: "s-2",
          data: "execution failed",
        })

        const snapshot =
          timeline.snapshot()

        expect(
          snapshot.terminal,
        ).toBe(true)

        expect(
          snapshot.failed,
        ).toBe(true)

        expect(
          snapshot.latest?.kind,
        ).toBe("error")
      },
    )

    it(
      "clears sequence and events",
      () => {
        const timeline =
          new ExecutionEventTimeline()

        const first =
          timeline.append({
            type: "step",
            session_id: "s-1",
            data: step,
          })

        timeline.clear()

        const second =
          timeline.append({
            type: "step",
            session_id: "s-1",
            data: step,
          })

        expect(
          timeline.count(),
        ).toBe(1)

        expect(first.id).toBe(1)
        expect(second.id).toBe(1)
      },
    )
  },
)
