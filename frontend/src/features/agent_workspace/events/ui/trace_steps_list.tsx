/** 步骤列表：把 agent_loop 的 trace 渲染成可读步骤流。
 *
 * 工业级契约：
 *   - 每步显示相对首步的时间偏移（+Xms）
 *   - 每步显示自身耗时（Xms，相对上一步）
 *   - 长参数截断显示
 */
import { useMemo } from "react"

export interface TraceStep {
  step: number
  thought?: string
  action?: string
  args?: Record<string, unknown>
  observation?: string
  remaining?: number
  repeated?: boolean
  done?: boolean
  ts_ms?: number
}

interface Props {
  trace: readonly TraceStep[]
}

export function TraceStepsList({ trace }: Props) {
  const items = useMemo(() => trace ?? [], [trace])

  // 基准时间：第一步的 ts_ms（没有就用最后一条的 ts_ms）
  const baseTs = useMemo(() => {
    for (const t of items) {
      if (typeof t.ts_ms === "number") return t.ts_ms
    }
    return 0
  }, [items])

  if (items.length === 0) return null

  return (
    <div className="trace-steps">
      {items.map((t, i) => {
        const offset =
          baseTs && typeof t.ts_ms === "number"
            ? t.ts_ms - baseTs
            : null

        // 上一步的时间（用于算单步耗时）
        const prevTs = (() => {
          for (let j = i - 1; j >= 0; j--) {
            if (typeof items[j].ts_ms === "number") {
              return items[j].ts_ms as number
            }
          }
          return null
        })()

        const duration =
          prevTs !== null && typeof t.ts_ms === "number"
            ? t.ts_ms - prevTs
            : i === 0 && typeof t.ts_ms === "number"
              ? 0
              : null

        return (
          <div
            key={i}
            className={
              "trace-step" +
              (t.done ? " trace-step--done" : "") +
              (t.repeated ? " trace-step--repeated" : "")
            }
          >
            <div className="trace-step__head">
              <span className="trace-step__num">步骤 {t.step}</span>
              {t.action && (
                <code className="trace-step__action">
                  {t.action}({formatArgs(t.args)})
                </code>
              )}
              {t.done && <span className="trace-step__badge">完成</span>}
              {t.repeated && (
                <span className="trace-step__badge trace-step__badge--warn">
                  重复拦截
                </span>
              )}
              {offset !== null && (
                <span className="trace-step__time" title="相对首步偏移">
                  +{offset}ms
                </span>
              )}
              {duration !== null && duration > 0 && (
                <span className="trace-step__duration" title="本步耗时">
                  {duration}ms
                </span>
              )}
              {typeof t.remaining === "number" && t.remaining > 0 && (
                <span className="trace-step__remaining">
                  剩 {t.remaining} 步
                </span>
              )}
            </div>
            {t.thought && (
              <div className="trace-step__thought">💭 {t.thought}</div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function formatArgs(args?: Record<string, unknown>): string {
  if (!args || Object.keys(args).length === 0) return ""
  return Object.entries(args)
    .map(([k, v]) => {
      let s = JSON.stringify(v)
      if (typeof s !== "string") s = String(s)
      if (s.length > 44) {
        s = s.slice(0, 22) + "…" + s.slice(-18)
      }
      return `${k}=${s}`
    })
    .join(", ")
}
