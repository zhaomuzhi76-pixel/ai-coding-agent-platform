/** MCP 管理主面板（Dify 风格：Servers 卡片 + Tools 网格 + 预设） */
import { useCallback, useEffect, useState } from "react"

import { ServerList } from "./server_list"
import { ServerForm } from "./server_form"
import { ToolCard, type ToolItem } from "./ToolCard"
import { CustomToolModal, type CustomToolPayload } from "./CustomToolModal"
import type { ServerItem, ServerConfigDTO } from "../../core/api/mcp_client_api"

const API = "/api/mcp"
const API_CLIENT = "/api/mcp_client"

async function _json<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!r.ok) throw new Error(`${r.status} ${path}`)
  return r.json()
}

async function _fetchServers(): Promise<ServerItem[]> {
  try {
    const d = await _json<any>(`${API_CLIENT}/servers`)
    return d?.data?.servers ?? d?.servers ?? []
  } catch { return [] }
}

async function _fetchServerTools(sid: string): Promise<ToolItem[]> {
  try {
    const d = await _json<any>(`${API_CLIENT}/servers/${encodeURIComponent(sid)}/tools`)
    const tools = d?.data?.tools ?? d?.tools ?? []
    return tools.map((t: any) => ({
      name: t.namespaced_name || t.raw_name || t.name,
      description: `MCP 工具 · 来自 ${sid}`,
      category: `mcp:${sid}`,
      exposed: true,
      param_count: 0,
    }))
  } catch { return [] }
}

export function McpDashboard() {
  const [builtinTools, setBuiltinTools] = useState<ToolItem[]>([])
  const [customTools, setCustomTools] = useState<ToolItem[]>([])
  const [remoteTools, setRemoteTools] = useState<ToolItem[]>([])
  const [servers, setServers] = useState<ServerItem[]>([])
  const [disabled, setDisabled] = useState<Set<string>>(new Set())
  const [customOpen, setCustomOpen] = useState(false)
  const [formOpen, setFormOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState("")

  const refresh = useCallback(async () => {
    try {
      const [tR, cR, dR, sv] = await Promise.all([
        _json<{ tools: ToolItem[] }>(`${API}/tools`),
        _json<{ tools: ToolItem[] }>(`${API}/custom-tools`),
        _json<{ disabled: string[] }>(`${API}/tools/disabled`),
        _fetchServers(),
      ])
      setBuiltinTools(tR.tools ?? [])
      setCustomTools(cR.tools ?? [])
      setDisabled(new Set(dR.disabled ?? []))
      setServers(sv)

      // 聚合所有 server 的工具
      const allRemote: ToolItem[] = []
      for (const s of sv) {
        const sid = s.config?.id
        if (!sid) continue
        const tools = await _fetchServerTools(sid)
        allRemote.push(...tools)
      }
      setRemoteTools(allRemote)
      setErr("")
    } catch (e) {
      setErr(String(e))
    }
  }, [])

  useEffect(() => { void refresh() }, [refresh])

  const onToggle = async (name: string, enable: boolean) => {
    try {
      await _json(`${API}/tools/${name}/toggle`, {
        method: "POST",
        body: JSON.stringify({ enabled: enable }),
      })
    } catch {}
    await refresh()
  }

  const onDeleteCustom = async (name: string) => {
    if (!window.confirm(`删除自定义工具 ${name}？`)) return
    try { await _json(`${API}/custom-tools/${name}`, { method: "DELETE" }) } catch {}
    await refresh()
  }

  const onCreateCustom = async (p: CustomToolPayload) => {
    try {
      await _json(`${API}/custom-tools`, {
        method: "POST", body: JSON.stringify(p),
      })
    } catch {}
    setCustomOpen(false)
    await refresh()
  }

  const onAddServer = async (cfg: Omit<ServerConfigDTO, "enabled"> & { enabled?: boolean }) => {
    setBusy(true)
    try {
      await _json(`${API_CLIENT}/servers`, {
        method: "POST", body: JSON.stringify({ ...cfg, enabled: true }),
      })
      setFormOpen(false)
      await refresh()
    } catch (e) {
      setErr(`添加失败: ${e}`)
    } finally {
      setBusy(false)
    }
  }

  const onReconnect = async (sid: string) => {
    try {
      await _json(`${API_CLIENT}/servers/${sid}/reconnect`, { method: "POST" })
    } catch {}
    await refresh()
  }

  const onRemove = async (sid: string) => {
    if (!window.confirm(`删除 server ${sid}？`)) return
    try { await _json(`${API_CLIENT}/servers/${sid}`, { method: "DELETE" }) } catch {}
    await refresh()
  }

  const allTools = [...builtinTools, ...customTools, ...remoteTools]
  const enabledCount = allTools.filter((t) => !disabled.has(t.name)).length

  return (
    <div className="mcp-dashboard">
      <header className="mcp-topbar">
        <h2>🔌 MCP 服务器 / 工具</h2>
        <div className="mcp-kpi">
          <span>Servers <b>{servers.length}</b></span>
          <span>Tools <b>{allTools.length}</b></span>
          <span>启用 <b>{enabledCount}</b></span>
        </div>
      </header>

      {err && <div className="mcp-err">{err}</div>}

      <section className="mcp-section">
        <div className="mcp-section-head">
          <h3>MCP Servers（外部连接）</h3>
          <button className="mcp-btn-primary" onClick={() => setFormOpen(true)}>
            + 添加 Server
          </button>
        </div>
        <ServerList
          servers={servers}
          onReconnect={onReconnect}
          onRemove={onRemove}
          onViewTools={(sid) => {
            const el = document.getElementById(`mcp-tool-${sid}`)
            if (el) el.scrollIntoView({ behavior: "smooth" })
          }}
        />

      </section>

      <section className="mcp-section">
        <div className="mcp-section-head">
          <h3>工具库（{allTools.length}）</h3>
          <button className="mcp-btn-primary"
                  onClick={() => setCustomOpen(true)}>
            + 自定义工具
          </button>
        </div>
        <div className="mcp-tool-grid">
          {allTools.map((t) => (
            <ToolCard
              key={t.name}
              tool={{ ...t, disabled: disabled.has(t.name) }}
              onToggle={onToggle}
              onDelete={t.custom ? onDeleteCustom : undefined}
            />
          ))}
        </div>
        {allTools.length === 0 && (
          <div className="mcp-empty">
            暂无工具 · 添加 MCP Server 或创建自定义工具
          </div>
        )}
      </section>

      {formOpen && (
        <div className="mcp-modal-mask" onClick={() => setFormOpen(false)}>
          <div className="mcp-modal mcp-modal--wide"
               onClick={(e) => e.stopPropagation()}>
            <h3>新增 MCP Server</h3>
            <ServerForm
              busy={busy}
              onCancel={() => setFormOpen(false)}
              onSubmit={onAddServer}
            />
          </div>
        </div>
      )}

      <CustomToolModal
        open={customOpen}
        onClose={() => setCustomOpen(false)}
        onSubmit={onCreateCustom}
      />
    </div>
  )
}

export default McpDashboard
