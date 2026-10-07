/** 微调产出模型卡片（含送 RAG） */
import { useEffect, useState } from "react"

export interface AdapterItem {
  adapter_id: string
  base_model?: string
  recipe_name?: string
  dataset_id?: string
  size_mb?: number
  loss?: number
  created_at?: number
}

interface Props {
  adapter: AdapterItem
  onDeploy: (id: string) => void
  onDelete: (id: string) => void
}

export function AdapterCard({ adapter, onDeploy, onDelete }: Props) {
  const [ragStatus, setRagStatus] = useState<"unknown" | "no" | "yes">("unknown")
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    fetch(`/api/finetune/adapters/${encodeURIComponent(adapter.adapter_id)}/rag-status`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setRagStatus(d?.indexed ? "yes" : "no"))
      .catch(() => setRagStatus("no"))
  }, [adapter.adapter_id])

  const sendToRag = async () => {
    setBusy(true)
    try {
      const r = await fetch(
        `/api/finetune/adapters/${encodeURIComponent(adapter.adapter_id)}/to-rag`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
      )
      const d = await r.json()
      if (d.ok) setRagStatus("yes")
      else alert("送 RAG 失败: " + (d.detail || d.error || "unknown"))
    } catch (e) {
      alert("送 RAG 失败: " + String(e))
    } finally {
      setBusy(false)
    }
  }

  const shortBase = (adapter.base_model || "?").split("/").pop()

  return (
    <div className="ft-adapter-card">
      <div className="ft-adapter-head">
        <span className="ft-adapter-name">🎯 {adapter.adapter_id.slice(0, 20)}</span>
        {ragStatus === "yes" && <span className="ft-tag-rag">已入 RAG</span>}
      </div>
      <div className="ft-adapter-meta">
        <span>🧠 {shortBase}</span>
        {adapter.recipe_name && <span>🍳 {adapter.recipe_name}</span>}
      </div>
      {adapter.loss != null && (
        <div className="ft-adapter-loss">
          loss: <b>{Number(adapter.loss).toFixed(4)}</b>
        </div>
      )}
      <div className="ft-adapter-actions">
        <button onClick={() => onDeploy(adapter.adapter_id)}>部署</button>
        <button className={ragStatus === "yes" ? "ok" : "primary"}
                disabled={busy || ragStatus === "yes"}
                onClick={sendToRag}>
          {ragStatus === "yes" ? "✅ 已送 RAG" : busy ? "送 RAG 中…" : "送入 RAG"}
        </button>
        <button className="danger" onClick={() => onDelete(adapter.adapter_id)}>删除</button>
      </div>
    </div>
  )
}

export default AdapterCard
