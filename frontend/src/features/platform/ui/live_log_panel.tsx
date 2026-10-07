import { useEffect, useRef } from "react"

export interface LiveEvent {
  event: string
  text?: string
  name?: string
  files?: string[]
  plan?: string
  proposal_id?: string
  reason?: string
}

const EVENT_COLORS: Record<string, string> = {
  stage: "#76a9ff",
  token: "#e6edf3",
  related_files: "#4fd69a",
  plan: "#e3b86d",
  done: "#4fd69a",
  error: "#ef8585",
}

function formatLine(e: LiveEvent): string {
  switch (e.event) {
    case "stage":
      return `▶ ${e.name ?? ""}`
    case "related_files":
      return `📎 相关文件：${(e.files ?? []).join(", ")}`
    case "plan":
      return `📋 计划：${e.plan ?? ""}`
    case "done":
      return `✅ 完成 proposal=${e.proposal_id ?? ""}`
    case "error":
      return `❌ ${e.reason ?? ""}`
    case "token":
      return e.text ?? ""
    default:
      return `[${e.event}]`
  }
}

export function LiveLogPanel(props: { events: LiveEvent[] }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight
    }
  }, [props.events])

  if (props.events.length === 0) return null

  return (
    <div
      style={{
        marginTop: 12,
        padding: "10px 12px",
        background: "#0b1119",
        border: "1px solid var(--line)",
        borderRadius: 8,
        maxHeight: 220,
        overflow: "auto",
        fontFamily: "ui-monospace, monospace",
        fontSize: 11,
        lineHeight: 1.55,
      }}
      ref={ref}
    >
      <div
        style={{
          fontSize: 10,
          color: "var(--muted)",
          textTransform: "uppercase",
          letterSpacing: 0.5,
          marginBottom: 6,
        }}
      >
        实时日志（{props.events.length}）
      </div>
      {props.events.map((e, i) => (
        <div
          key={i}
          style={{
            color: EVENT_COLORS[e.event] ?? "var(--text-soft)",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            display: e.event === "token" ? "inline" : "block",
          }}
        >
          {formatLine(e)}
        </div>
      ))}
    </div>
  )
}
