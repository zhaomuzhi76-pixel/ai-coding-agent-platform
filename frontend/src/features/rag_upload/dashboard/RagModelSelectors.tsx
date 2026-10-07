/** RAG 模型配置卡片（工业级） */
import { useCallback, useEffect, useState } from "react"
import { Badge } from "../../../app/ui/industrial"

interface ModelItem {
  id: string
  provider: string
  display_name: string
  is_local: boolean
}

interface Props { onChange?: (modelId: string) => void }

export function RagModelSelectors({ onChange }: Props = {}) {
  const [embeddings, setEmbeddings] = useState<ModelItem[]>([])
  const [rerankers, setRerankers] = useState<ModelItem[]>([])
  const [embModel, setEmbModel] = useState("")
  const [rrkModel, setRrkModel] = useState("")
  const [rrkEnabled, setRrkEnabled] = useState(true)
  const [msg, setMsg] = useState("")

  const load = useCallback(async () => {
    try {
      const r = await fetch("/api/rag/config-options")
      const d = await r.json()
      setEmbeddings(d.embeddings ?? [])
      setRerankers(d.rerankers ?? [])
      const cur = d.current ?? {}
      const initial = cur.embedding_model || d.embeddings?.[0]?.id || ""
      setEmbModel(initial)
      onChange?.(initial)
      setRrkModel(cur.reranker_model || d.rerankers?.[0]?.id || "")
      setRrkEnabled(cur.reranker_enabled ?? true)
    } catch (e) { setMsg(`加载失败: ${e}`) }
  }, [])
  useEffect(() => { void load() }, [load])

  const save = async () => {
    try {
      const r = await fetch("/api/rag/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          embedding_model: embModel,
          reranker_model: rrkModel,
          reranker_enabled: rrkEnabled,
        }),
      })
      const d = await r.json()
      setMsg(d.ok ? "✅ 已保存" : "❌ 保存失败")
      setTimeout(() => setMsg(""), 2500)
    } catch (e) { setMsg(`❌ ${e}`) }
  }

  return (
    <div className="ind-card" style={{ padding: 16 }}>
      <div style={{ fontSize: 12, color: "var(--text-soft)",
                    textTransform: "uppercase", letterSpacing: .5,
                    marginBottom: 12 }}>
        模型配置
      </div>

      <div className="rag-cfg-row">
        <label className="rag-cfg-label">向量模型</label>
        <select className="ind-select" value={embModel}
                onChange={(e) => { setEmbModel(e.target.value); onChange?.(e.target.value) }}>
          {embeddings.length === 0 && (
            <option value="">（无可选 · 去配置中心测试链路）</option>
          )}
          {embeddings.map((m) => (
            <option key={`${m.provider}:${m.id}`} value={m.id}>
              {m.is_local ? "🖥 " : "☁ "}{m.display_name} · {m.provider}
            </option>
          ))}
        </select>
        {embeddings.length > 0 && (
          <Badge tone="success">{embeddings.length} 个可用</Badge>
        )}
      </div>

      <div className="rag-cfg-row">
        <label className="rag-cfg-label">重排序模型</label>
        <select className="ind-select" value={rrkModel}
                disabled={!rrkEnabled}
                onChange={(e) => setRrkModel(e.target.value)}>
          {rerankers.length === 0 && (
            <option value="">（无可选 · 去配置中心测试链路）</option>
          )}
          {rerankers.map((m) => (
            <option key={`${m.provider}:${m.id}`} value={m.id}>
              {m.is_local ? "🖥 " : "☁ "}{m.display_name} · {m.provider}
            </option>
          ))}
        </select>
        {rerankers.length > 0 && (
          <Badge tone={rrkEnabled ? "success" : "muted"}>
            {rrkEnabled ? "已启用" : "已禁用"}
          </Badge>
        )}
      </div>

      <div className="rag-cfg-foot">
        <label style={{ display: "flex", gap: 6, alignItems: "center",
                        fontSize: 12, color: "var(--text-soft)" }}>
          <input type="checkbox" checked={rrkEnabled}
                 onChange={(e) => setRrkEnabled(e.target.checked)} />
          启用重排序（提高召回精度）
        </label>
        <div style={{ marginLeft: "auto", display: "flex",
                      gap: 10, alignItems: "center" }}>
          {msg && <span style={{ fontSize: 12, color: "var(--success)" }}>{msg}</span>}
          <button className="ind-btn ind-btn--primary" onClick={save}>
            保存配置
          </button>
        </div>
      </div>
    </div>
  )
}

export default RagModelSelectors
