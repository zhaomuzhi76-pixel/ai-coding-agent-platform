/**
 * RAG 独立 Tab（通用知识库）。
 *
 * 职责：
 *   - 索引：文本 / JSONL 数据集
 *   - 检索：query → 向量 + rerank
 *   - 状态：条数 / 向量库 / embedding / reranker
 */
import { useCallback, useEffect, useState } from "react"

import {
  ragApi,
  type RagHit,
  type RagStatus,
} from "../../../../core/api/rag_api"
import { useI18n } from "../../../../core/i18n/i18n"
import { RagMultimodalPanel } from "../../../../features/rag_multimodal/rag_multimodal_panel"
import { RagUploadPanel } from "../../../../features/rag_upload/rag_upload_panel"
import { DraftReview } from "../../../../features/l23_review"
import { RecallTest } from "../../../../features/l23_review"
import { MemoryPanel } from "../../../../features/memory/memory_panel"
import {
  Badge, EmptyState, IndustrialPage, KpiCard, KpiRow,
} from "../../../ui/industrial"

import type { RagPageRenderProps } from "./render.props";
// Auto-extracted render function for RagPage.

export function renderRagPage(props: RagPageRenderProps) {
  const { busy, dsPath, ftReport, hits, msg, onClear, onIndexAllFinetune, onIndexDataset, onIndexTexts, onQuery, q, refresh, setDsPath, setQ, setTextsInput, setTopK, setUseRerank, status, t, textsInput, topK, useRerank } = props;
  void busy;
  return (

      <IndustrialPage>
        <h2 style={{ margin: "0 0 6px" }}>{t("rag.title")}</h2>
        <p style={{ margin: "0 0 16px", opacity: 0.6, fontSize: 12 }}>
          {t("rag.subtitle")}
        </p>

        <KpiRow>
          <KpiCard
            label="索引条数"
            value={status ? String(status.count) : "—"}
          />
          <KpiCard label="向量库" value={status?.collection ?? "—"} />
          <KpiCard label="Embedding" value={status?.embedding.model ?? "—"} />
          <KpiCard
            label="Reranker"
            value={(() => {
              const h = status?.reranker.health
              if (!h) return "—"
              if (!h.ok) return "离线"
              if (h.mode === "local") {
                return h.count ? `本地 · ${h.count}` : "本地"
              }
              if (h.mode === "http") return "HTTP 9033"
              return "在线"
            })()}
          />
        </KpiRow>

        {msg && (
          <div style={{
            margin: "12px 0", padding: "8px 12px", borderRadius: 6,
            background: "rgba(118,169,255,.06)",
            border: "1px solid rgba(118,169,255,.25)",
            fontSize: 12,
          }}>{msg}</div>
        )}

        {/* 索引区 */}
        <section style={{ marginTop: 20 }}>
          <h3 style={{ fontSize: 13, margin: "0 0 8px", opacity: 0.7 }}>
            写入索引
          </h3>
          <div style={{ display: "grid", gap: 12 }}>
            <div className="ind-card" style={{ padding: 12, borderColor: "#7aa2f7" }}>
              <div style={{ fontSize: 13, marginBottom: 4 }}>
                ⚡ 一键索引所有微调数据集
              </div>
              <div style={{ fontSize: 11, opacity: 0.6, marginBottom: 8 }}>
                复用微调 Tab 里所有 JSONL 数据集（幂等：重复索引不会膨胀）
              </div>
              <button
                className="ind-btn ind-btn--primary"
                disabled={busy !== null}
                onClick={() => void onIndexAllFinetune()}
              >{busy === "ft-index" ? "索引中…" : "一键索引"}</button>
              {ftReport && (
                <div style={{ marginTop: 8, fontSize: 12, opacity: 0.8 }}>
                  数据集 {ftReport.dataset_count} ·
                  新增 {ftReport.total_indexed} chunk ·
                  跳过 {ftReport.skipped} · 失败 {ftReport.failed} ·
                  向量库合计 {ftReport.collection_total}
                </div>
              )}
            </div>

            <div className="ind-card" style={{ padding: 12 }}>
              <div style={{ fontSize: 12, marginBottom: 6, opacity: 0.7 }}>
                文本（每行一段）
              </div>
              <textarea
                className="ind-input"
                value={textsInput}
                onChange={(e) => setTextsInput(e.target.value)}
                placeholder={"Python 是解释型语言...\nRust 强调内存安全..."}
                style={{ width: "100%", minHeight: 80 }}
              />
              <button
                className="ind-btn"
                style={{ marginTop: 8 }}
                disabled={busy !== null}
                onClick={() => void onIndexTexts()}
              >{busy === "texts" ? "索引中…" : "索引文本"}</button>
            </div>

            <div className="ind-card" style={{ padding: 12 }}>
              <div style={{ fontSize: 12, marginBottom: 6, opacity: 0.7 }}>
                JSONL 数据集绝对路径
              </div>
              <input
                className="ind-input"
                value={dsPath}
                onChange={(e) => setDsPath(e.target.value)}
                placeholder="/home/.../datasets/xxx.jsonl"
                style={{ width: "100%" }}
              />
              <button
                className="ind-btn"
                style={{ marginTop: 8 }}
                disabled={busy !== null}
                onClick={() => void onIndexDataset()}
              >{busy === "dataset" ? "索引中…" : "索引数据集"}</button>
            </div>
          </div>
        </section>

        {/* 检索区 */}
        <section style={{ marginTop: 24 }}>
          <h3 style={{ fontSize: 13, margin: "0 0 8px", opacity: 0.7 }}>
            检索测试
          </h3>
          <div className="ind-card" style={{ padding: 12 }}>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <input
                className="ind-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") void onQuery() }}
                placeholder="输入查询…"
                style={{ flex: 1, minWidth: 200 }}
              />
              <input
                className="ind-input"
                type="number"
                min={1}
                max={50}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value) || 5)}
                style={{ width: 70 }}
              />
              <label style={{
                display: "flex", alignItems: "center", gap: 4, fontSize: 12,
              }}>
                <input
                  type="checkbox"
                  checked={useRerank}
                  onChange={(e) => setUseRerank(e.target.checked)}
                />
                Rerank
              </label>
              <button
                className="ind-btn"
                disabled={busy === "query"}
                onClick={() => void onQuery()}
              >{busy === "query" ? "检索中…" : "检索"}</button>
              <button
                className="ind-btn"
                disabled={busy !== null}
                onClick={() => void onClear()}
              >清空</button>
            </div>

            <div style={{ marginTop: 12 }}>
              {hits.length === 0 ? (
                <EmptyState title="暂无结果" icon="◇" />
              ) : (
                hits.map((h, i) => (
                  <div
                    key={h.chunk_id || i}
                    style={{
                      padding: "8px 10px", marginBottom: 6, borderRadius: 6,
                      background: "rgba(118,169,255,.04)",
                      border: "1px solid rgba(118,169,255,.15)",
                      fontSize: 12,
                    }}
                  >
                    <div style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                      <Badge tone="info">{h.score.toFixed(4)}</Badge>
                      {h.source && (
                        <span style={{ opacity: 0.6 }}>{h.source}</span>
                      )}
                    </div>
                    <div style={{ whiteSpace: "pre-wrap" }}>{h.text}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <RagMultimodalPanel />
        <RagUploadPanel onUploaded={() => void refresh()} />
        <DraftReview />
        <RecallTest />
        <MemoryPanel />
      </IndustrialPage>
  );
}
