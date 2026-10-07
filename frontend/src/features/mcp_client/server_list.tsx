/** MCP server 列表。职责：渲染 server 状态 + 操作（重连/删除）。
 * 不调 API 细节（父组件传回调）。 */
import { useState } from "react"

import type { ServerItem } from "../../core/api/mcp_client_api"
import { Badge, EmptyState } from "../../app/ui/industrial"

interface Props {
  servers: ServerItem[]
  onReconnect: (sid: string) => Promise<void>
  onRemove: (sid: string) => Promise<void>
  onViewTools: (sid: string) => void
  busy?: boolean
}

const STATUS_TONE: Record<string, "success" | "muted" | "danger" | "info"> = {
  online: "success", disconnected: "muted",
  connecting: "info", error: "danger",
}

export function ServerList({
  servers, onReconnect, onRemove, onViewTools, busy,
}: Props) {
  const [expanded, setExpanded] = useState<string | null>(null)

  if (servers.length === 0) {
    return <EmptyState title="未连接远端"
                        hint="点击添加，连接 stdio 或 http MCP server"
                        icon="⛭" />
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {servers.map(({ config: c, status: s }) => {
        const isOpen = expanded === c.id
        return (
          <div key={c.id} className="ind-card" style={{ padding: 10 }}>
            <div style={{
              display: "flex", justifyContent: "space-between",
              alignItems: "center", gap: 12,
            }}>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: 8,
                  marginBottom: 4,
                }}>
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{c.name}</span>
                  <Badge tone={STATUS_TONE[s.status] ?? "muted"}>
                    {s.status}
                  </Badge>
                  <span style={{
                    fontSize: 11, opacity: 0.5,
                    fontFamily: "ui-monospace, monospace",
                  }}>{c.id}</span>
                </div>
                <div style={{ fontSize: 11, opacity: 0.6 }}>
                  {c.transport === "stdio"
                    ? `⌘ ${c.command} ${(c.args ?? []).join(" ")}`
                    : `🌐 ${c.url}`}
                </div>
                <div style={{ fontSize: 11, opacity: 0.5, marginTop: 2 }}>
                  工具 {s.tool_count} · 命名空间 {c.namespace}
                  {s.error && <span style={{ color: "#ef8585" }}> · {s.error.slice(0, 60)}</span>}
                </div>
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                <button className="ind-btn" disabled={busy}
                  onClick={() => { setExpanded(isOpen ? null : c.id); onViewTools(c.id) }}>
                  {isOpen ? "收起" : "工具"}
                </button>
                <button className="ind-btn" disabled={busy}
                  onClick={() => void onReconnect(c.id)}>重连</button>
                <button className="ind-btn" disabled={busy}
                  onClick={() => void onRemove(c.id)}>删除</button>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
