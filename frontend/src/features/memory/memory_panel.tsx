/** Agent 记忆面板 —— 含作用域分组。 */
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  memoryApi, SCOPE_LABEL,
  type Preference, type RuleScope,
} from "../../core/api/memory_api"
import "./memory_panel.css"

const KIND_LABEL: Record<string, string> = {
  language: "语言", style: "风格", tech_stack: "技术栈",
  code_style: "代码风格", domain: "领域", workflow: "工作流",
  dislike: "避免项", other: "其它",
}
const SCOPE_ORDER: RuleScope[] = ["global", "project", "session"]

export function MemoryPanel() {
  const [prefs, setPrefs] = useState<Preference[]>([])
  const [msg, setMsg] = useState("")
  const [busy, setBusy] = useState(false)
  const [filter, setFilter] = useState<RuleScope | "all">("all")
  const [newKind, setNewKind] = useState("code_style")
  const [newKey, setNewKey] = useState("")
  const [newVal, setNewVal] = useState("")
  const [newScope, setNewScope] = useState<RuleScope>("global")
  const [draft, setDraft] = useState("")
  const [showAdd, setShowAdd] = useState(false)
  const [showExtract, setShowExtract] = useState(false)

  const load = useCallback(async () => {
    try {
      const r = await memoryApi.list(0)
      setPrefs(r.preferences)
    } catch (e) { setMsg("加载失败: " + String(e)) }
  }, [])

  useEffect(() => { void load() }, [load])

  const filtered = useMemo(
    () => filter === "all" ? prefs
      : prefs.filter((p) => (p.scope || "global") === filter),
    [prefs, filter],
  )

  const grouped = useMemo(() => {
    const out: Record<string, Preference[]> = {}
    for (const p of filtered) {
      const k = p.scope || "global"
      if (!out[k]) out[k] = []
      out[k].push(p)
    }
    return out
  }, [filtered])

  const onAdd = async () => {
    if (!newKey.trim() || !newVal.trim()) { setMsg("key/value 必填"); return }
    setBusy(true); setMsg("")
    try {
      await memoryApi.add({ kind: newKind, key: newKey.trim(),
        value: newVal.trim(), confidence: 80, scope: newScope })
      setNewKey(""); setNewVal(""); setShowAdd(false)
      await load(); setMsg("✅ 已添加")
    } catch (e) { setMsg(String(e)) } finally { setBusy(false) }
  }

  const onExtract = async () => {
    if (!draft.trim()) return
    setBusy(true); setMsg("")
    try {
      const r = await memoryApi.extract(draft, true)
      setDraft(""); setShowExtract(false); await load()
      setMsg(`✅ 提取 ${r.stored} 条候选`)
    } catch (e) { setMsg(String(e)) } finally { setBusy(false) }
  }

  const onDelete = async (id: number) => {
    try { await memoryApi.remove(id); await load() }
    catch (e) { setMsg(String(e)) }
  }

  const onConf = async (id: number, c: number) => {
    try { await memoryApi.setConfidence(id, c); await load() }
    catch (e) { setMsg(String(e)) }
  }

  const onScope = async (id: number, s: RuleScope) => {
    try { await memoryApi.setScope(id, s, ""); await load() }
    catch (e) { setMsg(String(e)) }
  }

  return (
    <section className="mem-panel">
      <div className="mem-panel__head">
        <div>
          <div className="mem-panel__title">Agent 记忆</div>
          <div className="mem-panel__sub">
            从对话学到的规则，按作用域分组（全局 / 项目 / 会话）
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="ind-btn" onClick={() => setShowAdd(v => !v)}>+ 新增</button>
          <button className="ind-btn" onClick={() => setShowExtract(v => !v)}>
            {showExtract ? "收起" : "从对话提取"}
          </button>
          <button className="ind-btn" onClick={() => void load()}>刷新</button>
        </div>
      </div>

      {msg && <div className="mem-msg">{msg}</div>}

      <div className="mem-filter">
        <button className={filter === "all" ? "active" : ""}
                onClick={() => setFilter("all")}>全部 {prefs.length}</button>
        {SCOPE_ORDER.map((s) => {
          const n = prefs.filter((p) => (p.scope || "global") === s).length
          return (
            <button key={s} className={filter === s ? "active" : ""}
                    onClick={() => setFilter(s)}>
              {SCOPE_LABEL[s]} {n}
            </button>
          )
        })}
      </div>

      {showAdd && (
        <div className="mem-form">
          <select value={newKind} onChange={(e) => setNewKind(e.target.value)}>
            {Object.entries(KIND_LABEL).map(([k, v]) =>
              <option key={k} value={k}>{v}</option>)}
          </select>
          <input placeholder="key（如 forbid）" value={newKey}
                 onChange={(e) => setNewKey(e.target.value)} />
          <input placeholder="value（如 print）" value={newVal}
                 onChange={(e) => setNewVal(e.target.value)} />
          <select value={newScope} onChange={(e) =>
            setNewScope(e.target.value as RuleScope)}>
            <option value="global">全局</option>
            <option value="project">项目</option>
            <option value="session">会话</option>
          </select>
          <button className="ind-btn" disabled={busy}
                  onClick={() => void onAdd()}>保存</button>
        </div>
      )}

      {showExtract && (
        <div className="mem-extract">
          <textarea placeholder="粘贴一段对话，Agent 从中学习偏好…"
                    value={draft} onChange={(e) => setDraft(e.target.value)}
                    rows={3} />
          <button className="ind-btn" disabled={busy}
                  onClick={() => void onExtract()}>
            {busy ? "提取中…" : "提取偏好"}
          </button>
        </div>
      )}

      {SCOPE_ORDER.map((s) => {
        const items = grouped[s] || []
        if (items.length === 0) return null
        return (
          <div key={s} className="mem-group">
            <div className="mem-group__title">
              {SCOPE_LABEL[s]} <span>{items.length}</span>
            </div>
            {items.map((p) => (
              <div key={p.id}
                   className={"mem-item" + (p.auto_applied ? " mem-item--auto" : "")}>
                <div className="mem-item__head">
                  <span className="mem-kind">{KIND_LABEL[p.kind] || p.kind}</span>
                  <span className="mem-key">{p.key}</span>
                  <span className={"mem-badge" + (p.auto_applied ? " mem-badge--on" : "")}>
                    {p.auto_applied ? "已应用" : `置信 ${p.confidence}`}
                  </span>
                </div>
                <div className="mem-val">{p.value}</div>
                <div className="mem-item__foot">
                  <div className="mem-conf-bar">
                    <div className="mem-conf-fill"
                         style={{ width: `${p.confidence}%` }} />
                  </div>
                  <div className="mem-actions">
                    <select value={p.scope || "global"}
                            onChange={(e) => void onScope(p.id, e.target.value as RuleScope)}
                            className="mem-scope-sel">
                      <option value="global">全局</option>
                      <option value="project">项目</option>
                      <option value="session">会话</option>
                    </select>
                    <button onClick={() => void onConf(p.id,
                      Math.min(100, p.confidence + 10))}>↑</button>
                    <button onClick={() => void onConf(p.id,
                      Math.max(0, p.confidence - 10))}>↓</button>
                    <button className="mem-del"
                            onClick={() => void onDelete(p.id)}>删除</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )
      })}

      {filtered.length === 0 && (
        <div className="mem-empty">
          {prefs.length === 0 ? "暂无记忆。点「从对话提取」开始。"
            : "当前作用域下暂无规则。"}
        </div>
      )}
    </section>
  )
}
