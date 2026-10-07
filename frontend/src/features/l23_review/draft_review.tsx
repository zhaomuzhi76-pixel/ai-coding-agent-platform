/** 审核门 · 可视化召回（Dify 风格） */
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import {
  l23ReviewApi,
  type DraftChunk,
  type ReviewPageData,
} from "../../core/api/l23_review_api"

import "./l23_review.css"

interface JobSummary {
  job_id: string
  chunk_count: number
  preview: string
}

import { renderDraftReview } from "./_draft_review_parts/render";

export function DraftReview() {
  const [jobs, setJobs] = useState<JobSummary[]>([])
  const [currentJob, setCurrentJob] = useState<string | null>(null)
  const [query, setQuery] = useState("审核门")
  const [page, setPage] = useState<ReviewPageData | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)

  const loadJobs = useCallback(async () => {
    try {
      const r = await l23ReviewApi.listJobs()
      setJobs(r.jobs)
    } catch (e) {
      setMsg("加载列表失败: " + String(e))
    }
  }, [])

  useEffect(() => { void loadJobs() }, [loadJobs])

  const loadPage = useCallback(async (jid: string, q: string) => {
    try {
      const r = await l23ReviewApi.page(jid, q)
      setPage(r)
      setSelected(new Set(
        r.chunks.filter((c) => c.is_hit).map((c) => c.chunk_id),
      ))
    } catch (e) {
      setMsg(String(e))
    }
  }, [])

  useEffect(() => {
    if (!currentJob) return
    if (timerRef.current) window.clearTimeout(timerRef.current)
    timerRef.current = window.setTimeout(() => {
      void loadPage(currentJob, query)
    }, 300)
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
    }
  }, [currentJob, query, loadPage])

  const onSeed = async () => {
    setBusy(true); setMsg(null)
    try {
      await l23ReviewApi.seed(`demo-${Date.now()}`)
      await loadJobs()
      setMsg("✅ 已生成演示草稿")
    } catch (e) {
      setMsg(String(e))
    } finally { setBusy(false) }
  }

  const toggle = (cid: string) => {
    const n = new Set(selected)
    n.has(cid) ? n.delete(cid) : n.add(cid)
    setSelected(n)
  }

  const onApprove = async () => {
    if (!page) return
    setBusy(true); setMsg(null)
    try {
      const r = await l23ReviewApi.approve(page.job_id, Array.from(selected))
      setMsg(`✅ 通过 ${r.written} 块`)
      setPage(null); setCurrentJob(null)
      await loadJobs()
    } catch (e) { setMsg(String(e)) } finally { setBusy(false) }
  }

  const onReject = async () => {
    if (!page) return
    setBusy(true); setMsg(null)
    try {
      await l23ReviewApi.reject(page.job_id)
      setMsg("已拒绝")
      setPage(null); setCurrentJob(null)
      await loadJobs()
    } catch (e) { setMsg(String(e)) } finally { setBusy(false) }
  }

  return renderDraftReview({ busy, currentJob, jobs, loadJobs, msg, onApprove, onReject, onSeed, page, query, selected, setCurrentJob, setPage, setQuery, toggle });
}

function ChunkCard({ chunk, query, selected, onToggle }: {
  chunk: DraftChunk
  query: string
  selected: boolean
  onToggle: () => void
}) {
  const html = useMemo(
    () => highlight(chunk.content, query),
    [chunk.content, query],
  )
  return (
    <div className={"l23-chunk" + (chunk.is_hit ? "" : " l23-chunk--miss")}>
      <div className="l23-chunk__head">
        <label className="l23-chunk__check">
          <input type="checkbox" checked={selected} onChange={onToggle} />
          <span className="l23-chunk__id">{chunk.chunk_id}</span>
        </label>
        <div className="l23-chunk__badges">
          <span className={"l23-rank" + (chunk.is_hit ? " l23-rank--hit" : "")}>
            {chunk.is_hit ? `#${chunk.rank}` : "未召回"}
          </span>
          <span className="l23-score">
            RRF {chunk.fused.toFixed(4)}
          </span>
        </div>
      </div>
      <div className="l23-chunk__content"
           dangerouslySetInnerHTML={{ __html: html }} />
      <div className="l23-bars">
        <Bar label={`BM25  ${chunk.bm25.toFixed(2)}`}
             pct={chunk.bm25_bar} kind="bm25" />
        <Bar label={`Reranker  ${chunk.rerank.toFixed(4)}`}
             pct={chunk.rerank_bar} kind="rerank" />
      </div>
    </div>
  )
}

function Bar({ label, pct, kind }: {
  label: string; pct: number; kind: "bm25" | "rerank"
}) {
  const w = Math.max(0, Math.min(100, pct * 100))
  return (
    <div className="l23-bar">
      <div className="l23-bar__label">
        <span>{label}</span>
        <span>{w.toFixed(0)}%</span>
      </div>
      <div className="l23-bar__track">
        <div className={`l23-bar__fill l23-bar__fill--${kind}`}
             style={{ width: `${w}%` }} />
      </div>
    </div>
  )
}

function highlight(text: string, query: string): string {
  const esc = (s: string) => s
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  const safe = esc(text)
  const terms = query.split(/\s+/).map((t) => t.trim()).filter((t) => t.length >= 2)
  if (terms.length === 0) return safe
  let out = safe
  for (const t of terms) {
    const re = new RegExp(`(${t.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")})`, "gi")
    out = out.replace(re, "<mark>$1</mark>")
  }
  return out
}
