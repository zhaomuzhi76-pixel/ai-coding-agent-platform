import { useCallback, useEffect, useState } from "react"

import {
  providersApi, type CallRecord,
} from "../../../../core/api/providers_api"
import type { CostStats, BucketStats } from "../../../../core/contracts/cost"
import {
  Badge, EmptyState, Sparkline,
} from "../../../../app/ui/industrial"

import { ModelStatsTable } from "../model_stats_table"
import {
  TimeSelector, rangeToDays, type TimeRange,
} from "../time_selector"

import "../llm_calls_panel.css"

function timeHHMM(ts: number): string {
  const d = new Date(ts * 1000)
  return [d.getHours(), d.getMinutes(), d.getSeconds()]
    .map((n) => String(n).padStart(2, "0"))
    .join(":")
}

import type { LlmCallsPanelRenderProps } from "./render.props";
// Auto-extracted render function for LlmCallsPanel.

export function renderLlmCallsPanel(props: LlmCallsPanelRenderProps) {
  const { error, fmtCost, local, localCalls, online, onlineCalls, range, records, setRange, stats, sumCalls, timeHHMM, total, trend } = props;
  void error;
  return (

      <section className="llm-panel">
        <div style={{
          display: "flex", alignItems: "center",
          gap: 10, marginBottom: 12,
        }}>
          <h3 style={{
            fontSize: 13, margin: 0,
            color: "var(--text-soft)", fontWeight: 500,
          }}>
            LLM 调用统计
          </h3>
          <TimeSelector value={range} onChange={setRange} />
          <span style={{
            marginLeft: "auto", fontSize: 11, color: "var(--muted)",
            fontFamily: "ui-monospace, monospace",
          }}>
            {total?.calls ?? 0} 次调用 · {fmtCost(online?.cost ?? 0)} 线上成本
          </span>
        </div>

        {error && (
          <div style={{
            padding: "8px 12px", marginBottom: 10, borderRadius: 6,
            background: "rgba(239,133,133,.08)",
            border: "1px solid rgba(239,133,133,.3)",
            color: "var(--danger)", fontSize: 11,
          }}>
            {error}
          </div>
        )}

        {/* 线上/本地分布条 */}
        {sumCalls > 0 && (
          <div style={{ marginBottom: 12 }}>
            <div className="llm-panel__bar">
              <div
                className="llm-panel__bar-seg"
                style={{
                  width: `${(onlineCalls / sumCalls) * 100}%`,
                  background: "#76a9ff",
                }}
              />
              <div
                className="llm-panel__bar-seg"
                style={{
                  width: `${(localCalls / sumCalls) * 100}%`,
                  background: "#4fd69a",
                }}
              />
            </div>
            <div style={{
              display: "flex", justifyContent: "space-between",
              fontSize: 11, color: "var(--muted)",
              marginTop: 4, fontFamily: "ui-monospace, monospace",
            }}>
              <span>■ 线上 {onlineCalls} · {fmtCost(online?.cost ?? 0)}</span>
              <span>■ 本地 {localCalls}（无成本）</span>
            </div>
          </div>
        )}

        {/* 模型统计表 */}
        <details open style={{ marginBottom: 16 }}>
          <summary style={{
            fontSize: 12, cursor: "pointer",
            color: "var(--muted)",
            textTransform: "uppercase", letterSpacing: 0.4,
            padding: "4px 0",
          }}>
            模型维度统计（{stats ? Object.keys(stats.by_model).length : 0} 个模型）
          </summary>
          <div style={{ marginTop: 8 }}>
            {stats && Object.keys(stats.by_model).length > 0 ? (
              <ModelStatsTable models={stats.by_model} />
            ) : (
              <EmptyState
                title="暂无调用"
                hint="发起一次平台提案后显示"
                icon="◆"
              />
            )}
          </div>
        </details>

        {/* 按 role 分组 */}
        {stats && Object.keys(stats.by_role).length > 0 && (
          <details open style={{ marginBottom: 16 }}>
          <summary style={{
            fontSize: 12, cursor: "pointer",
            color: "var(--muted)",
            textTransform: "uppercase", letterSpacing: 0.4,
            padding: "4px 0",
          }}>
            按 Role 分组（{Object.keys(stats.by_role).length}）
          </summary>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: 8, marginTop: 8, marginBottom: 0,
          }}>
            {Object.entries(stats.by_role as Record<string, BucketStats>).map(([role, v]) => (
              <div key={role} style={{
                padding: "8px 10px", borderRadius: 6,
                background: "var(--panel-2)",
                border: "1px solid var(--line)",
              }}>
                <div style={{
                  fontSize: 10, color: "var(--muted)",
                  textTransform: "uppercase", letterSpacing: 0.4,
                }}>
                  {role}
                </div>
                <div style={{
                  fontSize: 13, marginTop: 4,
                  fontFamily: "ui-monospace, monospace",
                }}>
                  {v.calls} 次 · {fmtCost(v.cost)}
                </div>
              </div>
            ))}
          </div>
          </details>
        )}

        {trend.length > 1 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{
              fontSize: 11, color: "var(--muted)",
              textTransform: "uppercase", letterSpacing: 0.4,
              marginBottom: 4,
            }}>
              最近调用耗时（ms）
            </div>
            <Sparkline values={trend} height={28} />
          </div>
        )}

        {/* 最近调用记录 */}
        <details open>
          <summary style={{
            fontSize: 12, cursor: "pointer",
            color: "var(--muted)",
            textTransform: "uppercase", letterSpacing: 0.4,
            padding: "4px 0",
          }}>
            最近调用记录（{records.length}）
          </summary>
          <div style={{ marginTop: 8 }}>
        {records.length === 0 ? (
          <EmptyState title="暂无记录" icon="◇" />
        ) : (
          records.slice(-20).reverse().map((r) => (
            <div key={r.record_id} className="llm-panel__row">
              <span className="llm-panel__time">
                {timeHHMM(r.created_at)}
              </span>
              <span
                className={
                  "llm-panel__provider"
                  + (r.is_local ? " llm-panel__provider--local" : "")
                }
              >
                {r.provider}
              </span>
              <span className="llm-panel__model" title={r.model}>
                {r.model}
              </span>
              <span className="llm-panel__role">{r.role || "—"}</span>
              <span className="llm-panel__tokens">
                {r.input_tokens}→{r.output_tokens}
              </span>
              <span
                className={
                  "llm-panel__cost"
                  + (r.cost === 0 ? " llm-panel__cost--zero" : "")
                }
              >
                {r.is_local ? "—" : fmtCost(r.cost)}
              </span>
              <span className="llm-panel__latency">
                {r.latency_ms.toFixed(0)}ms
              </span>
              <span className="llm-panel__status">
                <Badge tone={r.success ? "success" : "danger"}>
                  {r.success ? "OK" : "ERR"}
                </Badge>
              </span>
            </div>
          ))
        )}
          </div>
        </details>
      </section>
  );
}
