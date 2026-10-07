/**
 * AI 助手页面（L10 工业级）。职责：左工具树 + 右聊天窗 + 顶部领域 chips。
 */
import { useCallback, useEffect, useRef, useState } from "react"

import {
  agentToolsApi, type AgentChatReply, type ToolItem,
} from "../../../core/api/agent_tools_api"
import { chatbotApi, type ModelGroups } from "../../../core/api/chatbot_api"
import { Badge } from "../../ui/industrial"
import { SelectionSelector } from "../../../features/chatbot/components/selection_selector"
import { ToolTree } from "../../../features/agent_tools/tool_tree"
import { ChatBubble } from "../../../features/agent_tools/chat_bubble"

const SID_KEY = "agent.session_id"
function ensureSid(): string {
  let s = window.localStorage.getItem(SID_KEY)
  if (!s) {
    s = "web-" + Math.random().toString(36).slice(2, 12)
    window.localStorage.setItem(SID_KEY, s)
  }
  return s
}

const DOMAIN_LABEL: Record<string, string> = {
  tcm: "中医", agriculture: "农业", finance: "金融",
  general: "通用", medicine: "医学", history: "历史", law: "法律",
  agriculture_tcm: "农业+中医",
}

interface Turn { user: string; reply?: AgentChatReply; error?: string }

export function ChatbotPage() {
  const [sid] = useState<string>(() => ensureSid())
  const [groups, setGroups] = useState<Record<string, ToolItem[]>>({})
  const [enabled, setEnabled] = useState<Set<string>>(new Set())
  const [total, setTotal] = useState(0)
  const [llmGroups, setLlmGroups] = useState<ModelGroups>({
    llm: [], image_gen: [], embedding: [], rerank: [],
  })
  const [llm, setLlm] = useState<string | null>(null)
  const [input, setInput] = useState("")
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [leftWidth, setLeftWidth] = useState<number>(() => {
    try {
      const v = localStorage.getItem("biancheng.chat.toolTreeWidth");
      return v ? Number(v) : 260;
    } catch { return 260; }
  })
  const scrollRef = useRef<HTMLDivElement>(null)

  const load = useCallback(async () => {
    try {
      const [tools, mounts] = await Promise.all([
        agentToolsApi.listTools(), agentToolsApi.getMounts(sid),
      ])
      setGroups(tools.groups); setTotal(tools.total)
      setEnabled(new Set(mounts.enabled)); setErr(null)
    } catch (e) { setErr(String(e)) }
    chatbotApi.listModels().then(setLlmGroups).catch(() => {})
  }, [sid])

  useEffect(() => { void load() }, [load])
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 9e9, behavior: "smooth" })
  }, [turns])

  // 单个工具切换
  const onToggle = useCallback(async (name: string) => {
    const next = new Set(enabled)
    if (next.has(name)) next.delete(name); else next.add(name)
    setEnabled(next)
    try { await agentToolsApi.setMounts(sid, { enable: Array.from(next) }) }
    catch (e) { setErr(String(e)) }
  }, [enabled, sid])

  // 领域批量切换（chips 和左侧标题共用）
  const toggleDomain = useCallback(async (domain: string) => {
    // [FIX] groups 的 key 是 group key，不是 domain
    // 需要遍历所有 groups 的所有 tools，筛出 domain 匹配的
    const matched: ToolItem[] = []
    for (const items of Object.values(groups)) {
      for (const t of items) {
        if ((t.domain || "general") === domain) matched.push(t)
      }
    }
    if (matched.length === 0) return
    const names = matched.map((t) => t.name)
    const allOn = names.every((n) => enabled.has(n))
    const next = new Set(enabled)
    if (allOn) {
      names.forEach((n) => next.delete(n))
    } else {
      names.forEach((n) => next.add(n))
    }
    setEnabled(next)   // 乐观更新
    try {
      await agentToolsApi.setMounts(sid, { enable: Array.from(next) })
    } catch (e) {
      setErr(String(e))
      // 失败回滚（可选）
    }
  }, [groups, enabled, sid])

  // 计算当前完全启用的领域清单（发给后端）
  const activeDomains = useCallback((): string[] => {
    const out: string[] = []
    for (const [domain, tools] of Object.entries(groups)) {
      if (tools.length > 0 && tools.every((t) => enabled.has(t.name))) {
        out.push(domain)
      }
    }
    return out
  }, [groups, enabled])

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text) return
    setBusy(true); setErr(null)
    setTurns((p) => [...p, { user: text }]); setInput("")
    try {
      const domains = activeDomains()
      const reply = await agentToolsApi.chat(sid, {
        text, provider: "ollama-local", model: (llm as string) || "__auto__",
        domains,
      })
      setTurns((p) => {
        const c = [...p]
        c[c.length - 1] = { ...c[c.length - 1], reply }
        return c
      })
    } catch (e) {
      setTurns((p) => {
        const c = [...p]
        c[c.length - 1] = { ...c[c.length - 1], error: String(e) }
        return c
      })
    } finally { setBusy(false) }
  }, [input, llm, sid, activeDomains])

  // [DRAG] 纯内联拖动（不用 useEffect，不丢帧）
  const beginDrag = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startW = leftWidth
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
    const onMove = (ev: MouseEvent) => {
      const next = Math.max(180, Math.min(600, startW + ev.clientX - startX))
      setLeftWidth(next)
    }
    const onUp = () => {
      document.removeEventListener("mousemove", onMove)
      document.removeEventListener("mouseup", onUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
    document.addEventListener("mousemove", onMove)
    document.addEventListener("mouseup", onUp)
  }, [leftWidth])

  // chips 状态
  const domainStats = Object.entries(groups).map(([domain, tools]) => {
    const onCount = tools.filter((t) => enabled.has(t.name)).length
    return { domain, total: tools.length, on: onCount, allOn: tools.length > 0 && onCount === tools.length }
  })

  return (
    <div style={{
      display: "grid", gridTemplateRows: "auto 1fr", height: "100%",
      minHeight: "calc(100vh - 64px)",
    }}>
      {/* 顶部栏 */}
      <div style={{
        padding: "12px 20px", borderBottom: "1px solid rgba(118,169,255,.1)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        gap: 12, flexWrap: "wrap",
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18 }}>AI 助手</h2>
          <div style={{ fontSize: 11, opacity: 0.55, marginTop: 2 }}>
            多领域 Agent · 工具自主调度 · 会话 {sid.slice(0, 14)}
          </div>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          {/* 领域 chips */}
          <div style={{ display: "flex", gap: 4, alignItems: "center",
                        padding: "2px 8px", borderRadius: 16,
                        background: "rgba(118,169,255,.06)" }}>
            <span style={{ fontSize: 10, color: "#6b7280" }}>领域</span>
            {domainStats.map((d) => (
              <button
                key={d.domain}
                type="button"
                onClick={() => void toggleDomain(d.domain)}
                title={d.allOn ? `取消全选 ${DOMAIN_LABEL[d.domain] ?? d.domain}`
                               : `全选 ${DOMAIN_LABEL[d.domain] ?? d.domain}`}
                style={{
                  padding: "2px 10px", borderRadius: 12,
                  border: "1px solid " + (d.allOn ? "#2563eb" : "#33333a"),
                  background: d.allOn ? "rgba(37,99,235,.2)" : "transparent",
                  color: d.allOn ? "#93c5fd" : "#9a9aa0",
                  fontSize: 11, cursor: "pointer",
                }}>
                {DOMAIN_LABEL[d.domain] ?? d.domain}
                <span style={{ opacity: 0.6, marginLeft: 4 }}>
                  {d.on}/{d.total}
                </span>
              </button>
            ))}
          </div>
          <Badge tone="info">工具 {total}</Badge>
          <Badge tone={enabled.size > 0 ? "success" : "muted"}>
            已启用 {enabled.size}
          </Badge>
          <div style={{ minWidth: 220 }}>
            <SelectionSelector kind="llm" label="LLM"
              items={llmGroups.llm} value={llm} onChange={setLlm} />
          </div>
        </div>
      </div>

      {/* 主区：左树 + 右聊 */}
      <div style={{
        display: "grid",
        gridTemplateColumns: `${leftWidth}px 8px 1fr`,
        minHeight: 0,
        height: "100%",
        overflow: "hidden",
      }}>
        <aside style={{
          borderRight: "none",
          padding: 12, overflowY: "auto", overflowX: "hidden",
          minWidth: 0, width: "100%", boxSizing: "border-box",
        }}>
          <div style={{
            fontSize: 11, opacity: 0.5, letterSpacing: 0.5,
            marginBottom: 8, paddingLeft: 4,
          }}>工具挂载（点击领域名=批量开关）</div>
          <ToolTree
            groups={groups}
            enabled={enabled}
            onToggle={(n) => void onToggle(n)}
            onToggleDomain={(d) => void toggleDomain(d)}
            domainLabel={DOMAIN_LABEL}
            busy={busy}
          />
        </aside>

        <div
          onMouseDown={beginDrag}
          onDoubleClick={() => setLeftWidth(260)}
          title="拖动调整宽度 · 双击复位"
          style={{
            width: "100%",
            height: "100%",
            minHeight: "100%",
            cursor: "col-resize",
            position: "relative",
            background: "rgba(118,169,255,.08)",
            borderLeft: "1px solid rgba(118,169,255,.15)",
            borderRight: "1px solid rgba(118,169,255,.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            userSelect: "none",
          }}
        >
          <div style={{
            width: 2,
            height: 32,
            background: "#2563eb",
            borderRadius: 1,
            pointerEvents: "none",
          }} />
        </div>

        <main style={{ display: "grid", gridTemplateRows: "1fr auto", minHeight: 0, minWidth: 0 }}>
          <div ref={scrollRef} style={{
            padding: "20px 24px", overflowY: "auto",
            display: "grid", gap: 16, alignContent: "start",
          }}>
            {turns.length === 0 ? (
              <div style={{
                display: "flex", flexDirection: "column",
                alignItems: "center", justifyContent: "center",
                height: "100%", opacity: 0.4, gap: 8,
              }}>
                <div style={{ fontSize: 48 }}>🤖</div>
                <div style={{ fontSize: 13 }}>输入问题，Agent 自主调度工具回答</div>
                <div style={{ fontSize: 11 }}>
                  试试：气虚的主症是什么 · 小麦白粉病怎么防治 · 股票有什么特点
                </div>
              </div>
            ) : (
              turns.map((t, i) => <ChatBubble key={i} turn={t} />)
            )}
          </div>

          {err && (
            <div style={{
              padding: "6px 24px", fontSize: 12, color: "#ef8585",
              borderTop: "1px solid rgba(239,133,133,.3)",
            }}>{err}</div>
          )}

          <div style={{
            padding: "12px 24px 16px",
            borderTop: "1px solid rgba(118,169,255,.1)",
          }}>
            <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
              <textarea
                className="ind-input"
                rows={2}
                value={input}
                disabled={busy}
                placeholder="输入消息…（Ctrl+Enter 发送，Enter 换行）"
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) void send()
                }}
                style={{ flex: 1, resize: "none", fontSize: 13, lineHeight: 1.5 }}
              />
              <button
                className="ind-btn ind-btn--primary"
                disabled={busy || !input.trim()}
                onClick={() => void send()}
                style={{ minWidth: 80, height: 40 }}
              >{busy ? "处理中…" : "发送"}</button>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
