/**
 * 向量化执行时间线。职责：把 steps 按 phase 聚合成阶段视图。
 * 输入：steps[] + progress + createdAt
 * 输出：阶段行（完成/进行中/等待中）+ 折叠展开 + 实时进度
 */
import { useState } from "react"
import { Badge } from "../../../app/ui/industrial"

export interface JobStep {
  ts: number
  phase: string
  message: string
  detail?: Record<string, unknown>
}

export interface JobProgress {
  phase: string
  current: number
  total: number
  percent: number
  message?: string
}

interface Props {
  steps: JobStep[]
  progress?: JobProgress
  createdAt?: number
}

const PHASE_LABEL: Record<string, string> = {
  queued: "排队", saving: "保存原件", parsing: "解析文本",
  chunking: "切分文档", embedding: "生成向量", indexing: "写入向量库",
  finalizing: "切分文档", pending_review: "准备向量化",
  done: "已完成", failed: "失败", cancelled: "已取消",
}

interface PhaseGroup {
  phase: string
  steps: JobStep[]
  firstTs: number
  lastTs: number
}

function _group(steps: JobStep[]): PhaseGroup[] {
  const out: PhaseGroup[] = []
  for (const st of steps) {
    const last = out[out.length - 1]
    if (last && last.phase === st.phase) {
      last.steps.push(st); last.lastTs = st.ts
    } else {
      out.push({ phase: st.phase, steps: [st], firstTs: st.ts, lastTs: st.ts })
    }
  }
  return out
}

function _fmtDur(sec: number): string {
  if (sec < 0 || !isFinite(sec)) return "-"
  if (sec < 1) return `${(sec * 1000).toFixed(0)}ms`
  if (sec < 60) return `${sec.toFixed(1)}s`
  return `${Math.floor(sec / 60)}分${(sec % 60).toFixed(0)}秒`
}

function _fmtTs(sec: number): string {
  if (!sec) return "-"
  const d = new Date(sec * 1000); const p = (n: number) => String(n).padStart(2, "0")
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

export function JobStepsTimeline({ steps, progress, createdAt }: Props) {
  const groups = _group(steps)
  // 动态 phase 顺序：先按 steps 出现顺序，再补 progress.phase
  const order: string[] = []
  const seen = new Set<string>()
  for (const g of groups) if (!seen.has(g.phase)) { seen.add(g.phase); order.push(g.phase) }
  const curPhase = progress?.phase || ""
  if (curPhase && !seen.has(curPhase)) order.push(curPhase)

  const curIdx = order.indexOf(curPhase)

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div style={{ fontSize: 11, opacity: 0.55 }}>
        开始于 {createdAt ? _fmtTs(createdAt) : "-"} ·
        共 <b style={{ color: "#7aa2f7" }}>{steps.length}</b> 步 · 
        <b style={{ color: "#7aa2f7" }}> {order.length}</b> 阶段
      </div>

      {order.map((phase, idx) => {
        const g = groups.find((x) => x.phase === phase)
        const isActive = phase === curPhase
        const isDone = !!g && !isActive && idx < curIdx
        const isPending = !g && idx > curIdx
        return (
          <PhaseRow key={phase} phase={phase} group={g}
            isActive={isActive} isDone={isDone} isPending={isPending}
            progress={isActive ? progress : undefined} />
        )
      })}
    </div>
  )
}

interface RowProps {
  phase: string
  group?: PhaseGroup
  isActive: boolean
  isDone: boolean
  isPending: boolean
  progress?: JobProgress
}

function PhaseRow({ phase, group, isActive, isDone, isPending, progress }: RowProps) {
  const [open, setOpen] = useState(false)
  const label = PHASE_LABEL[phase] || phase
  const count = group?.steps.length || 0
  const elapsed = group ? (group.lastTs - group.firstTs) : 0
  const latest = group ? group.steps[group.steps.length - 1] : undefined
  const color = isActive ? "#e29e4a" : isDone ? "#7aa2f7" : "rgba(118,169,255,.18)"

  return (
    <div style={{ borderLeft: `3px solid ${color}`, paddingLeft: 12 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ fontSize: 14, color }}>
          {isDone ? "✓" : isActive ? "⏳" : isPending ? "○" : "·"}
        </span>
        <span style={{ fontSize: 13, fontWeight: 500 }}>{label}</span>
        {count > 0 && <Badge tone="muted">{count} 步</Badge>}
        {isActive && progress && progress.total > 0 && (
          <Badge tone="warning">
            {progress.current}/{progress.total} · {(progress.percent * 100).toFixed(1)}%
          </Badge>
        )}
        {isDone && elapsed > 0 && (
          <span style={{ marginLeft: "auto", fontSize: 11, opacity: 0.6 }}>
            耗时 {_fmtDur(elapsed)}
          </span>
        )}
      </div>

      {latest && (
        <div style={{ marginTop: 4, fontSize: 12, opacity: 0.78 }}>
          {latest.message}
          {latest.detail && Object.keys(latest.detail).length > 0 && (
            <span style={{ marginLeft: 8, fontSize: 11, opacity: 0.5,
                           fontFamily: "ui-monospace, monospace" }}>
              {JSON.stringify(latest.detail).slice(0, 100)}
            </span>
          )}
        </div>
      )}

      {isActive && progress && progress.total > 0 && (
        <div style={{ marginTop: 6, height: 4, background: "rgba(118,169,255,.1)",
                      borderRadius: 2, overflow: "hidden" }}>
          <div style={{ width: `${(progress.current / progress.total) * 100}%`,
                        height: "100%", background: "#e29e4a",
                        transition: "width .3s" }} />
        </div>
      )}

      {count > 1 && (
        <button className="ind-btn" onClick={() => setOpen(!open)}
          style={{ fontSize: 11, padding: "2px 8px", marginTop: 6 }}>
          {open ? "收起" : `展开 ${count} 步`}
        </button>
      )}

      {open && group && (
        <div style={{ marginTop: 8, display: "grid", gap: 3,
                      maxHeight: 260, overflowY: "auto",
                      padding: "6px 8px", background: "rgba(0,0,0,.2)",
                      borderRadius: 4 }}>
          {group.steps.map((st, i) => (
            <div key={i} style={{ display: "grid",
                                  gridTemplateColumns: "70px 1fr",
                                  gap: 8, fontSize: 11, opacity: 0.7 }}>
              <span style={{ fontFamily: "monospace" }}>{_fmtTs(st.ts)}</span>
              <span>{st.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default JobStepsTimeline
