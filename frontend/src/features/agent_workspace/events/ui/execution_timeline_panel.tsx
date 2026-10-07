import "./execution_timeline.css"
import { AnswerMarkdown } from "./answer_markdown"
import { TraceStepsList, type TraceStep } from "./trace_steps_list"
import "./answer_markdown.css"
import type {
  AgentRuntimeMessage,
} from "../../../../core/contracts/execution_event"
import {
  useExecutionTimeline,
} from "./execution_timeline_projection"

interface Props {
  messages: readonly AgentRuntimeMessage[]
}

export function ExecutionTimelinePanel(
  props: Props,
) {
  const timeline =
    useExecutionTimeline(props.messages)

  return (
    <section className="execution-timeline">
      <header className="execution-timeline-header">
        <div>
          <span>Execution Timeline</span>
          <strong>
            {timeline.events.length} events
          </strong>
        </div>

        <span
          className={
            timeline.failed
              ? "timeline-state timeline-state-error"
              : timeline.terminal
                ? "timeline-state timeline-state-done"
                : "timeline-state"
          }
        >
          {timeline.failed
            ? "FAILED"
            : timeline.terminal
              ? "COMPLETED"
              : "RUNNING"}
        </span>
      </header>

      <div className="execution-timeline-list">
        {timeline.events.length === 0 ? (
          <div className="execution-timeline-empty">
            Waiting for execution events
          </div>
        ) : (
          <FinalResultOrTrace events={timeline.events} />
        )}
      </div>
    </section>
  )
}

interface TimelineEvent {
  id: number
  type: string
  data: unknown
  receivedAt: number
}

function FinalResultOrTrace({
  events,
}: {
  events: readonly TimelineEvent[]
}) {
  // 找最新一条 result 事件
  const resultEvt = [...events]
    .reverse()
    .find((e) => e.type === "result")
  const resultData =
    resultEvt && typeof resultEvt.data === "object" && resultEvt.data !== null
      ? (resultEvt.data as Record<string, unknown>)
      : null

  // ── 情况 1: 尚未有 result → 显示运行中的步骤流 ──
  if (!resultData) {
    const stepEvents = events.filter((e) => e.type === "step")
    return (
      <div className="timeline-running">
        <TraceStepsList
          trace={stepEvents.map((e) => {
            const d = (e.data ?? {}) as Record<string, unknown>
            const inner = (d.data ?? d) as Record<string, unknown>
            return {
              step: (inner.step as number) ?? 0,
              thought: (inner.thought as string) ?? "",
              action: (inner.action as string) ?? "",
              args: (inner.args as Record<string, unknown>) ?? {},
              remaining: (inner.remaining as number) ?? undefined,
              repeated: Boolean(inner.repeated),
              done: Boolean(inner.done),
            }
          })}
        />
      </div>
    )
  }

  // ── 情况 2: 失败结果 ──
  if (resultData.success === false) {
    const err = String(resultData.error ?? "未知错误")
    return (
      <div className="timeline-error">
        <AnswerMarkdown text={`**执行失败**\n\n\`\`\`\n${err}\n\`\`\``} />
      </div>
    )
  }

  // ── 情况 3: query 结果（有 text 字段）──
  if (typeof resultData.text === "string" && resultData.text.trim()) {
    const qTrace: TraceStep[] = Array.isArray(resultData.trace)
      ? (resultData.trace as TraceStep[])
      : []
    return (
      <div className="timeline-final">
        {qTrace.length > 0 && <TraceStepsList trace={qTrace} />}
        <AnswerMarkdown text={resultData.text} />
      </div>
    )
  }

  // ── 情况 4: agent_loop 结果（有 answer + trace）──
  const trace: TraceStep[] = Array.isArray(resultData.trace)
    ? (resultData.trace as TraceStep[])
    : []
  const answer =
    typeof resultData.answer === "string" ? resultData.answer : ""

  return (
    <div className="timeline-final">
      {trace.length > 0 && <TraceStepsList trace={trace} />}
      <AnswerMarkdown text={answer} />
    </div>
  )
}
