/** 工具调用链展示。职责：渲染某轮对话的 tool_trace。 */
import type { ToolTraceEntry } from "../../core/api/agent_tools_api"

interface Props { trace: ToolTraceEntry[] }

export function ChatTrace({ trace }: Props) {
  if (!trace || trace.length === 0) return null
  return (
    <div style={{
      marginTop: 6, padding: "6px 8px", fontSize: 11,
      borderRadius: 4, background: "rgba(118,169,255,.05)",
      border: "1px solid rgba(118,169,255,.15)",
    }}>
      {trace.map((t, i) => (
        <div key={i} style={{
          padding: "3px 0",
          borderBottom: i < trace.length - 1 ? "1px dashed rgba(118,169,255,.15)" : "none",
        }}>
          <span style={{ color: t.ok ? "#7aa2f7" : "#ef8585" }}>
            {t.ok ? "✓" : "✗"}
          </span>{" "}
          <span style={{ fontFamily: "ui-monospace, monospace" }}>{t.action}</span>
          {" "}
          <span style={{ opacity: 0.6 }}>
            {JSON.stringify(t.args).slice(0, 60)}
          </span>
          <div style={{ opacity: 0.75, marginTop: 2, whiteSpace: "pre-wrap" }}>
            {t.observation.slice(0, 200)}
          </div>
        </div>
      ))}
    </div>
  )
}
