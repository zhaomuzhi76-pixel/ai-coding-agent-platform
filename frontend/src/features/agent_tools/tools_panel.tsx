/** 工具面板。职责：渲染分组工具 + 勾选/取消。 */
import type { ToolItem } from "../../core/api/agent_tools_api"

interface Props {
  groups: Record<string, ToolItem[]>
  enabled: Set<string>
  onToggle: (name: string) => void
  busy?: boolean
}

export function ToolsPanel({ groups, enabled, onToggle, busy }: Props) {
  const keys = Object.keys(groups).sort()
  if (keys.length === 0) {
    return <div style={{ opacity: 0.6, fontSize: 12 }}>暂无工具</div>
  }
  return (
    <div style={{ display: "grid", gap: 10 }}>
      {keys.map((k) => (
        <div key={k} style={{ display: "grid", gap: 4 }}>
          <div style={{ fontSize: 11, opacity: 0.55, letterSpacing: 0.5 }}>
            {k}（{groups[k].length}）
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {groups[k].map((t) => {
              const on = enabled.has(t.name)
              return (
                <label key={t.name} style={{
                  display: "flex", alignItems: "center", gap: 6,
                  padding: "4px 8px", borderRadius: 4, fontSize: 12,
                  background: on ? "rgba(118,169,255,.15)" : "rgba(255,255,255,.03)",
                  border: "1px solid " + (on ? "rgba(118,169,255,.4)" : "rgba(255,255,255,.08)"),
                  cursor: busy ? "not-allowed" : "pointer",
                }}>
                  <input type="checkbox" checked={on} disabled={busy}
                    onChange={() => onToggle(t.name)} />
                  <span title={t.description}>{t.name}</span>
                </label>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
