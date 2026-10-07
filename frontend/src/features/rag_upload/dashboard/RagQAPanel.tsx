/** 图文问答面板：一次 query 同时返回文字答案 + 图片。
 *
 * 职责：
 *   - 调 /api/rag/qa
 *   - 渲染 answer / citations / images
 *   - 图片点击原窗口打开
 * 不做：
 *   - 不做召回策展（RecallTestPanel 管）
 *   - 不做数据源选择（QA 全库检索）
 */
import { useState } from "react"
import { Badge, EmptyState } from "../../../app/ui/industrial"

interface Citation {
  chunk_id: string
  text?: string
  score?: number
  rerank_score?: number
  doc_title?: string
  page?: number
  source?: string
}

interface ImageRef {
  id: string
  class_name?: string
  latin?: string
  url?: string
  image_path?: string
  source?: string
  score?: number
}

interface QAResp {
  query: string
  answer: string
  citations: Citation[]
  images: ImageRef[]
  meta?: {
    n_citations?: number
    n_images?: number
    models?: Record<string, string>
  }
}

export function RagQAPanel() {
  const [query, setQuery] = useState("")
  const [kText, setKText] = useState(3)
  const [kImg, setKImg] = useState(8)
  const [resp, setResp] = useState<QAResp | null>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState("")
  const [elapsed, setElapsed] = useState(0)

  const ask = async () => {
    if (!query.trim() || busy) return
    setBusy(true); setMsg(""); setResp(null)
    const t0 = performance.now()
    try {
      const r = await fetch("/api/rag/qa", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query, k_text: kText, k_img: kImg, generate: true,
        }),
      })
      const d = await r.json()
      setElapsed(Math.round(performance.now() - t0))
      if (d.ok) setResp(d.data)
      else setMsg(d.detail || "失败")
    } catch (e) {
      setMsg(String(e))
    } finally { setBusy(false) }
  }

  const imgSrc = (im: ImageRef): string => {
    if (im.url) return im.url
    if (im.image_path) {
      const p = im.image_path.replace(/\\/g, "/")
      if (p.startsWith("data/")) return "/" + p
      return p
    }
    return ""
  }

  return (
    <div className="ind-card" style={{ padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
        图文问答 · 检索 + 生成 + 图片同返
      </div>
      <div style={{ fontSize: 11, color: "var(--text-soft)", marginBottom: 12 }}>
        输入问题 → 双路检索（文本 + 图片）→ 重排 → 生成答案 → 附引用和图
      </div>

      <div className="ind-toolbar">
        <input className="ind-input" value={query}
               placeholder="如：麻黄的功效 / 甘草长什么样 / 桂枝汤组成"
               onChange={(e) => setQuery(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && ask()} />
        <label style={{ fontSize: 12, color: "var(--text-soft)",
                        display: "flex", gap: 4, alignItems: "center" }}>
          文本 K
          <input className="ind-input" type="number" value={kText}
                 min={1} max={10} style={{ width: 50, flex: "none" }}
                 onChange={(e) => setKText(Number(e.target.value))} />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-soft)",
                        display: "flex", gap: 4, alignItems: "center" }}>
          图 K
          <input className="ind-input" type="number" value={kImg}
                 min={0} max={20} style={{ width: 50, flex: "none" }}
                 onChange={(e) => setKImg(Number(e.target.value))} />
        </label>
        <button className="ind-btn ind-btn--primary"
                disabled={busy || !query.trim()} onClick={ask}>
          {busy ? "生成中…" : "提问"}
        </button>
      </div>

      {msg && (
        <div style={{ padding: "6px 10px", marginTop: 10,
                      background: "rgba(239,133,133,.08)",
                      border: "1px solid rgba(239,133,133,.3)",
                      color: "#ef8585", borderRadius: 6, fontSize: 12 }}>
          {msg}
        </div>
      )}

      {!resp && !busy && (
        <EmptyState title="输入问题后点【提问】"
                    hint="示例：麻黄的功效 / 甘草长什么样 / 桂枝汤组成"
                    icon="💬" />
      )}

      {resp && (
        <>
          <div style={{ display: "flex", gap: 8, alignItems: "center",
                        marginTop: 12, marginBottom: 8, flexWrap: "wrap" }}>
            <Badge tone="info">{resp.meta?.n_citations ?? resp.citations.length} 引用</Badge>
            <Badge tone="success">{resp.meta?.n_images ?? resp.images.length} 图</Badge>
            {elapsed > 0 && (
              <span style={{ fontSize: 11, color: "var(--text-soft)" }}>
                耗时 {elapsed}ms
              </span>
            )}
          </div>

          {/* 答案 */}
          <div style={{
            padding: 12, borderRadius: 6, background: "#17171a",
            border: "1px solid #2a2a2e",
            fontSize: 13, lineHeight: 1.7,
            color: "#d8d8e0", whiteSpace: "pre-wrap", marginBottom: 12,
          }}>
            {resp.answer || "（无答案）"}
          </div>

          {/* 引用 */}
          {resp.citations.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 6 }}>
                引用（{resp.citations.length}）
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                {resp.citations.map((c, i) => (
                  <div key={c.chunk_id} style={{
                    padding: 8, borderRadius: 4, background: "#141416",
                    border: "1px solid #26262a", fontSize: 11,
                  }}>
                    <div style={{ display: "flex", gap: 8, marginBottom: 4,
                                  alignItems: "center", flexWrap: "wrap" }}>
                      <Badge tone="muted">[{i + 1}]</Badge>
                      {c.doc_title && (
                        <span style={{ color: "var(--text-soft)" }}>
                          {c.doc_title}{c.page ? ` p.${c.page}` : ""}
                        </span>
                      )}
                      {c.rerank_score != null && (
                        <span style={{ color: "#4fd69a" }}>
                          rerank {c.rerank_score.toFixed(3)}
                        </span>
                      )}
                    </div>
                    <div style={{ color: "#a8a8b0", lineHeight: 1.5 }}>
                      {(c.text || "").slice(0, 200)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 图片 */}
          {resp.images.length > 0 && (
            <div>
              <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 6 }}>
                图片（{resp.images.length}）
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {resp.images.map((im) => {
                  const src = imgSrc(im)
                  if (!src) return null
                  return (
                    <a key={im.id} href={src} target="_blank" rel="noreferrer"
                       title={`${im.class_name || ""} ${im.latin || ""}`}
                       style={{ textDecoration: "none" }}>
                      <div style={{ position: "relative", display: "inline-block" }}>
                        <img src={src} alt={im.class_name || im.id}
                             style={{
                               maxWidth: 140, maxHeight: 140,
                               borderRadius: 6, display: "block",
                               border: "1px solid rgba(118,169,255,.3)",
                               cursor: "zoom-in",
                             }} />
                        {im.class_name && (
                          <span style={{
                            position: "absolute", top: 4, left: 4,
                            background: "rgba(0,0,0,.65)", color: "#fff",
                            fontSize: 10, padding: "1px 6px", borderRadius: 3,
                          }}>{im.class_name}</span>
                        )}
                      </div>
                    </a>
                  )
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default RagQAPanel
