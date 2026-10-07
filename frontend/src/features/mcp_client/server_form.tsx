/** 添加 MCP server 表单（含第三方预设模板） */
import { useState } from "react"

import type { ServerConfigDTO } from "../../core/api/mcp_client_api"
import { MCP_PRESETS, type McpPreset } from "./presets"

type NewServer = Omit<ServerConfigDTO, "enabled"> & { enabled?: boolean }

interface Props {
  onSubmit: (cfg: NewServer) => Promise<void>
  onCancel: () => void
  busy?: boolean
}

export function ServerForm({ onSubmit, onCancel, busy }: Props) {
  const [id, setId] = useState("")
  const [name, setName] = useState("")
  const [transport, setTransport] = useState<"stdio" | "http">("stdio")
  const [command, setCommand] = useState("")
  const [argsText, setArgsText] = useState("")
  const [url, setUrl] = useState("")
  const [namespace, setNamespace] = useState("mcp")
  const [err, setErr] = useState<string | null>(null)

  const applyPreset = (p: McpPreset) => {
    setId(p.id)
    setName(p.name)
    setTransport(p.transport)
    setNamespace(p.id.replace(/-/g, "_"))
    if (p.transport === "stdio") {
      setCommand(p.command || "")
      setArgsText((p.args || []).join(" "))
    } else {
      setUrl(p.url || "")
    }
    setErr(null)
  }

  const submit = async () => {
    if (!id.trim()) { setErr("id 必填"); return }
    if (!name.trim()) { setErr("name 必填"); return }
    if (transport === "stdio" && !command.trim()) { setErr("stdio 需 command"); return }
    if (transport === "http" && !url.trim()) { setErr("http 需 url"); return }
    setErr(null)
    const args = argsText.split(/\s+/).map((x) => x.trim()).filter(Boolean)
    const cfg: NewServer = transport === "stdio"
      ? { id, name, transport, command, args, namespace, enabled: true }
      : { id, name, transport, url, namespace, enabled: true }
    try { await onSubmit(cfg) }
    catch (e) { setErr(String(e)) }
  }

  const row = (label: string, node: React.ReactNode) => (
    <label style={{ display: "grid", gap: 4, marginBottom: 8 }}>
      <span style={{ fontSize: 11, opacity: 0.6 }}>{label}</span>
      {node}
    </label>
  )

  return (
    <div style={{ display: "grid", gap: 6 }}>
      {err && (
        <div style={{
          padding: "6px 10px", borderRadius: 4, fontSize: 12,
          background: "rgba(239,133,133,.1)", color: "#ef8585",
          border: "1px solid rgba(239,133,133,.3)",
        }}>{err}</div>
      )}

      <div style={{ fontSize: 11, opacity: 0.6, marginTop: 2 }}>
        预设模板（点击一键填充）
      </div>
      <div className="mcp-preset-grid">
        {MCP_PRESETS.map((p) => (
          <button key={p.id} type="button"
                  className="mcp-preset-card"
                  onClick={() => applyPreset(p)}
                  title={p.description}>
            <span className="mcp-preset-icon">{p.icon}</span>
            <span className="mcp-preset-name">{p.name}</span>
          </button>
        ))}
      </div>

      <div style={{ fontSize: 11, opacity: 0.6, marginTop: 8 }}>
        手动配置
      </div>

      {row("ID", <input className="ind-input" value={id}
        onChange={(e) => setId(e.target.value)}
        placeholder="filesystem / github / fetch" />)}
      {row("显示名", <input className="ind-input" value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Filesystem MCP" />)}
      {row("传输方式", (
        <select className="ind-input" value={transport}
          onChange={(e) => setTransport(e.target.value as "stdio" | "http")}>
          <option value="stdio">stdio（本地子进程）</option>
          <option value="http">http（远端 URL）</option>
        </select>
      ))}

      {transport === "stdio" && (
        <>
          {row("命令", <input className="ind-input" value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="npx / python / node" />)}
          {row("参数（空格分隔）", (
            <input className="ind-input" value={argsText}
              onChange={(e) => setArgsText(e.target.value)}
              placeholder="-y @modelcontextprotocol/server-filesystem /tmp" />
          ))}
        </>
      )}

      {transport === "http" && (
        row("URL", <input className="ind-input" value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/mcp" />)
      )}

      {row("命名空间前缀", <input className="ind-input" value={namespace}
        onChange={(e) => setNamespace(e.target.value)}
        placeholder="mcp" />)}

      <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
        <button className="ind-btn ind-btn--primary"
          disabled={busy} onClick={() => void submit()}>
          {busy ? "连接中…" : "连接并添加"}
        </button>
        <button className="ind-btn" disabled={busy} onClick={onCancel}>取消</button>
      </div>
    </div>
  )
}

export default ServerForm
