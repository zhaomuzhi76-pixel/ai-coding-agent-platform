/**
 * JobStreamPanel：消费 useFinetuneJobs() 的事件流。
 *
 * Owns:
 *   - 事件列表渲染（最多 500 条，hook 已限流）
 *   - phase 徽章
 *   - 清空按钮
 *
 * Not:
 *   - 传输（finetune_job_socket 管）
 *   - 状态管理（use_finetune_jobs 管）
 *   - 训练控制（由其它组件负责）
 */
import { useEffect, useState } from "react"
import { useFinetuneJobs } from "./use_finetune_jobs"
import { onSelectJob, getSelectedJob } from "./job_selection_bus"
import { computeMetrics } from "./metrics_from_events"
import { Sparkline } from "../../../app/ui/industrial/sparkline"
import type { JobEvent } from "../ws/finetune_job_socket"

const PHASE_TONE: Record<string, string> = {
  connected: "success",
  connecting: "warning",
  reconnecting: "warning",
  closed: "danger",
  idle: "neutral",
}

function fmtTs(ts: number): string {
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString(undefined, { hour12: false })
}

function eventSummary(ev: JobEvent): string {
  const p = ev.payload || {}
  switch (ev.event_type) {
    case "progress":
      return `step ${p.step}/${p.total} · ${p.percent}% · loss=${p.loss}`
    case "log":
      return `[${p.level}] ${p.message}`
    case "epoch":
      return `epoch ${p.epoch}/${p.total_epochs} ${JSON.stringify(p.metrics)}`
    case "succeeded":
      return `succeeded → ${p.saved_to || "(no path)"}`
    case "failed":
      return `failed: ${p.error}`
    case "cancelled":
      return `cancelled: ${p.reason}`
    case "created":
      return `created job_id=${p.job_id}`
    case "started":
      return `started job_id=${p.job_id}`
    case "checkpoint":
      return `checkpoint step=${p.step} ${p.path}`
    case "eval":
      return `eval ${JSON.stringify(p.metrics)}`
    default:
      return JSON.stringify(p).slice(0, 120)
  }
}

export function JobStreamPanel() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(
    getSelectedJob(),
  )
  useEffect(() => onSelectJob(setSelectedJobId), [])
  const { events, phase, clear } = useFinetuneJobs(
    selectedJobId ? { jobId: selectedJobId } : {},
  )
  const metrics = computeMetrics(events)
  const tone = PHASE_TONE[phase] || "neutral"

  return (
    <div style={{
      marginTop: 16,
      border: "1px solid var(--border, #333)",
      borderRadius: 6,
      padding: 12,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontWeight: 600 }}>
          训练事件流
          <span
            data-tone={tone}
            style={{
              marginLeft: 8, padding: "2px 8px", borderRadius: 10, fontSize: 12,
              background: tone === "success" ? "#1b5e20"
                        : tone === "warning" ? "#7a4f00"
                        : tone === "danger"  ? "#7f1d1d"
                        : "#333",
              color: "#fff",
            }}
          >{phase}</span>
          <span style={{ marginLeft: 8, fontSize: 12, opacity: 0.6 }}>
            {events.length} 条
          </span>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {selectedJobId && (
            <>
              <span style={{ fontSize: 12, opacity: 0.7 }}>
                查看: <code>{selectedJobId}</code>
              </span>
              <button
                onClick={() => { setSelectedJobId(null); clear() }}
                style={{ fontSize: 12 }}
              >全部</button>
            </>
          )}
          <button onClick={clear} style={{ fontSize: 12 }}>清空</button>
        </div>
      </div>

      {metrics.losses.length > 0 && (
        <div style={{
          marginTop: 8, padding: "6px 8px", borderRadius: 4,
          background: "rgba(118,169,255,.04)",
          border: "1px solid rgba(118,169,255,.15)",
          fontSize: 11, display: "flex", alignItems: "center", gap: 14,
        }}>
          <span>
            loss: <b>{metrics.lastLoss.toFixed(4)}</b>
            <span style={{ opacity: 0.6, marginLeft: 6 }}>
              (best {metrics.bestLoss.toFixed(4)})
            </span>
          </span>
          <span>step: {metrics.lastStep}/{metrics.totalSteps}</span>
          <span>进度: {metrics.progress.toFixed(1)}%</span>
          <div style={{ flex: 1, maxWidth: 220 }}>
            <Sparkline values={metrics.losses} height={24} />
          </div>
        </div>
      )}

      <div style={{
        marginTop: 8, maxHeight: 260, overflowY: "auto",
        fontFamily: "monospace", fontSize: 12, lineHeight: 1.5,
      }}>
        {events.length === 0 ? (
          <div style={{ opacity: 0.5 }}>（暂无事件 · 提交训练任务后此处会实时刷新）</div>
        ) : (
          events.slice().reverse().map((ev) => (
            <div key={ev.event_id} style={{ display: "flex", gap: 8 }}>
              <span style={{ opacity: 0.5 }}>{fmtTs(ev.created_at)}</span>
              <span style={{ minWidth: 90, color: "#7dd3fc" }}>{ev.event_type}</span>
              <span>{eventSummary(ev)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
