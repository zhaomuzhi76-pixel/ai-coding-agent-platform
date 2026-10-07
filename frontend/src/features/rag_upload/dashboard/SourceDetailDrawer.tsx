/** 单文档完整内容抽屉：全屏展开 + 分页 + 字号切换。 */
import { memo, useEffect, useRef, useState } from "react"
import { Badge, Drawer } from "../../../app/ui/industrial"

interface ImageRef {
  id: string
  mime?: string
  url?: string
  b64?: string
  alt_text?: string
  source?: string
}

function imgSrc(a: ImageRef): string | null {
  if (a.url) return a.url
  if (a.b64) return `data:${a.mime ?? "image/png"};base64,${a.b64}`
  return null
}

interface Chunk {
  chunk_id: string
  text: string
  text_len: number
  page_no: number | null
  images?: ImageRef[]
}

interface Props {
  open: boolean
  title: string
  chunkIds: string[]
  matchValues: string[]
  onClose: () => void
  onChanged: () => void
}

export const SourceDetailDrawer = memo(function SourceDetailDrawer({
  open, title, chunkIds, matchValues, onClose, onChanged,
}: Props) {
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [dim, setDim] = useState(0)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState("")
  const [mode, setMode] = useState<"full" | "chunks">("full")
  const [fontSizeState, setFontSizeState] = useState<number>(16)
  const [lineHeight, setLineHeight] = useState<number>(2.0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 50

  const lastKeyRef = useRef<string>("")
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!open) return
    const key = `${chunkIds.length}|${matchValues.length}|${chunkIds[0] ?? ""}`
    if (lastKeyRef.current === key && chunks.length > 0) return
    lastKeyRef.current = key

    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setBusy(true)
    fetch("/api/rag/vectors/source-detail", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chunk_ids: chunkIds, match_values: matchValues }),
      signal: ctrl.signal,
    })
      .then((r) => r.json())
      .then((d) => {
        if (ctrl.signal.aborted) return
        setChunks(Array.isArray(d.chunks) ? d.chunks : [])
        setDim(d.embedding_dim ?? 0)
      })
      .catch((e) => {
        if (ctrl.signal.aborted) return
        setMsg(`加载失败: ${e}`)
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setBusy(false)
      })

    return () => { ctrl.abort() }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  useEffect(() => { setPage(1) }, [chunks.length])

  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", onEsc)
    return () => window.removeEventListener("keydown", onEsc)
  }, [onClose])

  const deleteChunk = async (cid: string) => {
    if (!window.confirm(`删除分块 ${cid}？`)) return
    try {
      await fetch("/api/rag/vectors/chunk/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chunk_id: cid }),
      })
      setChunks((prev) => prev.filter((c) => c.chunk_id !== cid))
      onChanged()
    } catch (e) { setMsg(`❌ ${e}`) }
  }

  const totalPages = Math.max(1, Math.ceil(chunks.length / PAGE_SIZE))
  const start = (page - 1) * PAGE_SIZE
  const pageChunks = chunks.slice(start, start + PAGE_SIZE)
  const pageText = pageChunks.map((c) => (c.text || "").trim())
                          .filter(Boolean).join("\n\n")
  const fullText = chunks.map((c) => (c.text || "").trim()).filter(Boolean).join("\n\n")
  const totalChars = fullText.length

  const copyAll = () => {
    navigator.clipboard.writeText(fullText).then(() => {
      setMsg("✅ 已复制全文")
      setTimeout(() => setMsg(""), 1500)
    })
  }

  return (
    <Drawer open={open} title={title || "完整数据"} onClose={onClose}
            className={"ind-drawer--wide" + (isFullscreen ? " ind-drawer--fullscreen" : "")}
            footer={
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <Badge tone="info">{chunks.length} 块</Badge>
                <Badge tone="success">{dim} 维</Badge>
                <Badge tone="muted">{totalChars} 字</Badge>
                {msg && <span style={{ fontSize: 11, color: "#4fd69a" }}>{msg}</span>}
                <button className="ind-btn" style={{ marginLeft: "auto" }} onClick={copyAll}>
                  复制全文
                </button>
                <button className="ind-btn" onClick={onClose}>关闭</button>
              </div>
            }>
      {/* 顶部展开按钮 */}
      <div className="drawer-toggle-bar"
           onClick={() => setIsFullscreen((v) => !v)}
           title={isFullscreen ? "点击退出全屏" : "点击进入全屏"}>
        <span className="drawer-toggle-bar__icon">{isFullscreen ? "▼" : "▲"}</span>
        <span className="drawer-toggle-bar__label">
          {isFullscreen ? "收起（退出全屏）" : "展开（全屏阅读）"}
        </span>
      </div>

      {/* 工具栏 */}
      <div className="ind-toolbar" style={{ marginBottom: 10 }}>
        <button className={"ind-btn" + (mode === "full" ? " ind-btn--primary" : "")}
                onClick={() => setMode("full")}>📄 完整内容</button>
        <button className={"ind-btn" + (mode === "chunks" ? " ind-btn--primary" : "")}
                onClick={() => setMode("chunks")}>🧩 分块明细</button>
        <span style={{ marginLeft: "auto", fontSize: 11, opacity: 0.6 }}>字号</span>
        {[14, 16, 18, 20].map((sz) => (
          <button key={sz}
                  className={"ind-btn" + (fontSizeState === sz ? " ind-btn--primary" : "")}
                  style={{ padding: "2px 8px", fontSize: 12 }}
                  onClick={() => setFontSizeState(sz)}>{sz}</button>
        ))}
        <span style={{ fontSize: 11, opacity: 0.6, marginLeft: 8 }}>行距</span>
        {[1.6, 1.8, 2.0, 2.4].map((lh) => (
          <button key={lh}
                  className={"ind-btn" + (lineHeight === lh ? " ind-btn--primary" : "")}
                  style={{ padding: "2px 8px", fontSize: 12 }}
                  onClick={() => setLineHeight(lh)}>{lh}</button>
        ))}
      </div>

      {busy && chunks.length === 0 && (
        <div style={{ padding: 24, textAlign: "center", opacity: 0.6 }}>加载中…</div>
      )}
      {!busy && chunks.length === 0 && (
        <div style={{ padding: 24, textAlign: "center", opacity: 0.6 }}>
          无分块数据
        </div>
      )}

      {/* 完整内容（分页） */}
      {mode === "full" && chunks.length > 0 && (
        <div style={{
          margin: 0, padding: 16, background: "#131316",
          borderRadius: 8, border: "1px solid #2a2a2e",
          fontSize: fontSizeState, lineHeight: lineHeight, color: "#d8d8e0",
          wordBreak: "break-word",
          fontFamily: "ui-sans-serif, system-ui",
          maxHeight: "calc(100vh - 260px)", overflowY: "auto",
          whiteSpace: "pre-wrap",
        }}>
          {pageText}
          {/* [IMG_FULL] 本页缩略图 */}
          {(() => {
            const imgs: ImageRef[] = []
            for (const c of pageChunks) {
              for (const im of (c.images ?? [])) imgs.push(im)
            }
            if (imgs.length === 0) return null
            return (
              <div style={{
                marginTop: 24, paddingTop: 16,
                borderTop: "1px dashed rgba(118,169,255,.25)",
              }}>
                <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 8 }}>
                  本页 {imgs.length} 张图：
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  {imgs.map((img) => {
                    const src = imgSrc(img)
                    if (!src) return null
                    return (
                      <a key={img.id} href={src} target="_blank"
                         rel="noreferrer" title={img.alt_text || img.id}>
                        <img src={src} alt={img.alt_text || img.id}
                             style={{
                               maxWidth: 180, maxHeight: 180,
                               borderRadius: 6, display: "block",
                               border: "1px solid rgba(118,169,255,.3)",
                               cursor: "zoom-in",
                             }} />
                      </a>
                    )
                  })}
                </div>
              </div>
            )
          })()}
        </div>
      )}

      {/* 分块明细（分页） */}
      {mode === "chunks" && chunks.length > 0 && (
        <div style={{ display: "grid", gap: 6 }}>
          {pageChunks.map((c, i) => (
            <div key={c.chunk_id} className="ind-card" style={{ padding: 10 }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center",
                            marginBottom: 6, flexWrap: "wrap" }}>
                <Badge tone="info">#{start + i + 1}</Badge>
                {c.page_no != null && <Badge tone="muted">第 {c.page_no} 页</Badge>}
                <span style={{ fontSize: 11, opacity: 0.6,
                               fontFamily: "ui-monospace, monospace" }}>
                  {c.chunk_id}
                </span>
                <span style={{ fontSize: 11, opacity: 0.6 }}>{c.text_len} 字</span>
                <button className="ind-btn"
                        style={{ marginLeft: "auto", padding: "2px 8px", fontSize: 11,
                                 borderColor: "#7f1d1d", color: "#fca5a5" }}
                        onClick={() => deleteChunk(c.chunk_id)}>删除</button>
              </div>
              <div style={{ fontSize: fontSizeState - 1, color: "#c8c8d0",
                            lineHeight: lineHeight }}>
                {c.text}
                {/* [IMG_RENDER] 缩略图 */}
                {c.images && c.images.length > 0 && (
                  <div style={{ display: "flex", gap: 8, marginTop: 8,
                                flexWrap: "wrap" }}>
                    {c.images.map((img) => {
                      const src = imgSrc(img)
                      if (!src) return null
                      return (
                        <a key={img.id} href={src} target="_blank"
                           rel="noreferrer" title={img.alt_text || img.id}>
                          <img src={src} alt={img.alt_text || img.id}
                               style={{
                                 maxWidth: 160, maxHeight: 160,
                                 borderRadius: 4, display: "block",
                                 border: "1px solid rgba(118,169,255,.3)",
                                 cursor: "zoom-in",
                               }} />
                        </a>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 分页控件 */}
      {chunks.length > 0 && (
        <div className="drawer-pagination">
          <button disabled={page <= 1} onClick={() => setPage(1)}>首页</button>
          <button disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}>上一页</button>
          <span className="drawer-pagination__info">{page} / {totalPages}</span>
          <button disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>下一页</button>
          <button disabled={page >= totalPages}
                  onClick={() => setPage(totalPages)}>末页</button>
          <span style={{ marginLeft: 16, opacity: 0.5 }}>
            共 {chunks.length} 条 · 每页 {PAGE_SIZE} 条
          </span>
        </div>
      )}
    </Drawer>
  )
})

export default SourceDetailDrawer
