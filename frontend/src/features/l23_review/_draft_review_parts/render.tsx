/** 审核门 · 可视化召回（Dify 风格） */
import { useCallback, useEffect, useMemo, useRef, useState } from "react"

import {
  l23ReviewApi,
  type DraftChunk,
  type ReviewPageData,
} from "../../../core/api/l23_review_api"

import "../l23_review.css"

interface JobSummary {
  job_id: string
  chunk_count: number
  preview: string
}

// Auto-extracted render function for DraftReview.
export interface DraftReviewRenderProps {
  busy: any
  currentJob: any
  jobs: any
  loadJobs: any
  msg: any
  onApprove: any
  onReject: any
  onSeed: any
  page: any
  query: any
  selected: any
  setCurrentJob: any
  setPage: any
  setQuery: any
  toggle: any
}

export function renderDraftReview(props: DraftReviewRenderProps) {
  const { busy, currentJob, jobs, loadJobs, msg, onApprove, onReject, onSeed, page, query, selected, setCurrentJob, setPage, setQuery, toggle } = props;
  void busy;
  return (

      <section className="l23-panel">
        <div className="l23-panel__head">
          <div>
            <div className="l23-panel__title">审核门 · 可视化召回</div>
            <div className="l23-panel__sub">
              实时预览草稿块被召回的情况（BM25 + Reranker）
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="ind-btn" disabled={busy} onClick={() => void loadJobs()}>
              刷新
            </button>
            <button className="ind-btn" disabled={busy} onClick={() => void onSeed()}>
              生成演示草稿
            </button>
          </div>
        </div>

        {msg && <div className="l23-msg">{msg}</div>}

        {!currentJob && (
          <div className="l23-jobs">
            {jobs.length === 0 ? (
              <div className="l23-empty">
                暂无待审核草稿 —— 点右上角「生成演示草稿」或上传文档
              </div>
            ) : (
              jobs.map((j) => (
                <button
                  key={j.job_id}
                  className="l23-job-card"
                  onClick={() => { setCurrentJob(j.job_id); setPage(null) }}
                >
                  <div className="l23-job-card__id">{j.job_id}</div>
                  <div className="l23-job-card__meta">{j.chunk_count} 块</div>
                  {j.preview && (
                    <div className="l23-job-card__preview">{j.preview}</div>
                  )}
                </button>
              ))
            )}
          </div>
        )}

        {currentJob && (
          <>
            <div className="l23-toolbar">
              <button
                className="ind-btn"
                onClick={() => { setCurrentJob(null); setPage(null) }}
              >
                ← 返回列表
              </button>
              <div className="l23-toolbar__job">job: {currentJob}</div>
            </div>

            <div className="l23-search">
              <span className="l23-search__icon">🔍</span>
              <input
                className="l23-search__input"
                placeholder="输入查询词，实时查看召回打分…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
              {page && (
                <span className="l23-search__meta">
                  {page.hit_count}/{page.total} 命中 · 已选 {selected.size}
                </span>
              )}
            </div>

            {page && (
              <>
                <div className="l23-chunks">
                  {page.chunks.map((c) => (
                    <ChunkCard
                      key={c.chunk_id}
                      chunk={c}
                      query={query}
                      selected={selected.has(c.chunk_id)}
                      onToggle={() => toggle(c.chunk_id)}
                    />
                  ))}
                </div>

                <div className="l23-actions l23-actions--sticky">
                  <button className="ind-btn l23-btn--primary"
                          disabled={busy} onClick={() => void onApprove()}>
                    通过选中的 {selected.size} 块
                  </button>
                  <button className="ind-btn l23-btn--danger"
                          disabled={busy} onClick={() => void onReject()}>
                    拒绝全部
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </section>
  );
}
