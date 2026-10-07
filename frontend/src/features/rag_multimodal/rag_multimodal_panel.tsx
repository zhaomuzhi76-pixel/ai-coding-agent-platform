/**
 * 图文混合 RAG 面板。职责：收集图文输入 / 展示图文命中。
 * 不直接 fetch（用 rag_api）、不做切片、不做向量化。
 */
import { useState } from "react"

import { ragApi } from "../../core/api/rag_api"
import { Badge, EmptyState } from "../../app/ui/industrial"

interface ImageOut {
  id: string
  mime: string
  source: string
  url?: string
  b64?: string
  alt_text?: string
}

interface Hit {
  chunk_id: string
  text: string
  score: number
  source: string
  images: ImageOut[]
}

function imgSrc(a: ImageOut): string | null {
  if (a.url) return a.url
  if (a.b64) return `data:${a.mime};base64,${a.b64}`
  return null
}

export function RagMultimodalPanel() {
  const [text, setText] = useState("")
  const [imgUrls, setImgUrls] = useState("")
  const [q, setQ] = useState("")
  const [limit, setLimit] = useState(5)
  const [busy, setBusy] = useState<string | null>(null)
  const [msg, setMsg] = useState<string | null>(null)
  const [hits, setHits] = useState<Hit[]>([])

  const parseUrls = (): Array<Record<string, unknown>> => {
    const out: Array<Record<string, unknown>> = []
    imgUrls.split(/\n|,/).map((x) => x.trim()).filter(Boolean).forEach((u, i) => {
      out.push({ id: `ui-img-${i}`, mime: "image/jpeg", url: u,
                 source: "indexed", alt_text: "" })
    })
    return out
  }

  const onIndex = async () => {
    if (!text.trim()) { setMsg("请填写文本"); return }
    setBusy("index"); setMsg(null)
    try {
      const imgs = parseUrls()
      const r = await ragApi.multimodalIndex({
        text: text.trim(), images: imgs.length > 0 ? imgs : undefined,
        source: "ui-multimodal",
      })
      setMsg(`已索引 ${r.indexed} chunk，图片 ${imgs.length} 张`)
      setText(""); setImgUrls("")
    } catch (e) { setMsg("失败: " + String(e)) }
    finally { setBusy(null) }
  }

  const onSearch = async () => {
    if (!q.trim()) return
    setBusy("search"); setMsg(null)
    try {
      const r = await ragApi.multimodalSearch({
        query: q.trim(), limit, rerank: true,
      })
      setHits(r.hits)
      if (r.hits.length === 0) setMsg("未命中")
    } catch (e) { setMsg("失败: " + String(e)) }
    finally { setBusy(null) }
  }

  return (
    <section style={{ marginTop: 24 }}>
      <h3 style={{ fontSize: 13, margin: "0 0 8px", opacity: 0.7 }}>
        图文混合索引 / 检索
      </h3>

      {msg && (
        <div style={{
          margin: "8px 0", padding: "6px 10px", borderRadius: 6,
          background: "rgba(118,169,255,.06)",
          border: "1px solid rgba(118,169,255,.25)", fontSize: 12,
        }}>{msg}</div>
      )}

      <div className="ind-card" style={{ padding: 12, marginBottom: 12 }}>
        <div style={{ fontSize: 12, marginBottom: 6, opacity: 0.7 }}>文本</div>
        <textarea
          className="ind-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="玉米是禾本科一年生草本植物..."
          style={{ width: "100%", minHeight: 60 }}
        />
        <div style={{ fontSize: 12, margin: "8px 0 6px", opacity: 0.7 }}>
          图片 URL（每行一个，可选）
        </div>
        <textarea
          className="ind-input"
          value={imgUrls}
          onChange={(e) => setImgUrls(e.target.value)}
          placeholder={"https://.../maize.jpg\nhttps://.../pepper.jpg"}
          style={{ width: "100%", minHeight: 50 }}
        />
        <button
          className="ind-btn ind-btn--primary"
          style={{ marginTop: 8 }}
          disabled={busy !== null}
          onClick={() => void onIndex()}
        >{busy === "index" ? "索引中…" : "写入图文索引"}</button>
      </div>

      <div className="ind-card" style={{ padding: 12 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            className="ind-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") void onSearch() }}
            placeholder="多模态检索…"
            style={{ flex: 1, minWidth: 200 }}
          />
          <input
            className="ind-input"
            type="number" min={1} max={50}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 5)}
            style={{ width: 70 }}
          />
          <button
            className="ind-btn"
            disabled={busy === "search"}
            onClick={() => void onSearch()}
          >{busy === "search" ? "检索中…" : "检索"}</button>
        </div>

        <div style={{ marginTop: 12 }}>
          {hits.length === 0 ? (
            <EmptyState title="暂无结果" icon="◇" />
          ) : (
            hits.map((h, i) => (
              <div key={h.chunk_id || i} style={{
                padding: "8px 10px", marginBottom: 6, borderRadius: 6,
                background: "rgba(118,169,255,.04)",
                border: "1px solid rgba(118,169,255,.15)", fontSize: 12,
              }}>
                <div style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                  <Badge tone="info">{h.score.toFixed(4)}</Badge>
                  {h.source && <span style={{ opacity: 0.6 }}>{h.source}</span>}
                  {h.images.length > 0 && (
                    <span style={{ opacity: 0.7 }}>📷 {h.images.length}</span>
                  )}
                </div>
                <div style={{ whiteSpace: "pre-wrap" }}>{h.text}</div>
                {h.images.length > 0 && (
                  <div style={{ display: "flex", gap: 6, marginTop: 6,
                                flexWrap: "wrap" }}>
                    {h.images.map((a) => {
                      const src = imgSrc(a)
                      return src ? (
                        <img key={a.id} src={src} alt={a.alt_text || a.id}
                          style={{ maxWidth: 120, borderRadius: 4,
                                   display: "block" }} />
                      ) : (
                        <span key={a.id} style={{ opacity: 0.6 }}>
                          [image {a.id}]
                        </span>
                      )
                    })}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  )
}
