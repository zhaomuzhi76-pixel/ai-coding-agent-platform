/**
 * computeMetrics：从 JobEvent[] 提取训练指标序列。
 *
 * Owns:
 *   - 过滤 progress 事件
 *   - 提取 steps / losses / lrs / percents
 *   - 计算 last / best / progress
 *
 * Not:
 *   - UI（面板管）
 *   - 事件订阅（useFinetuneJobs 管）
 */
import type { JobEvent } from "../ws/finetune_job_socket"

export interface JobMetrics {
  steps: number[]
  losses: number[]
  lrs: number[]
  percents: number[]
  lastLoss: number
  bestLoss: number
  lastStep: number
  totalSteps: number
  progress: number
}

export function computeMetrics(events: JobEvent[]): JobMetrics {
  const steps: number[] = []
  const losses: number[] = []
  const lrs: number[] = []
  const percents: number[] = []
  let lastStep = 0
  let totalSteps = 0
  let progress = 0

  for (const e of events) {
    if (e.event_type !== "progress") continue
    const p = e.payload as Record<string, unknown>
    const st = Number(p.step ?? 0)
    const tt = Number(p.total ?? 0)
    const ls = Number(p.loss ?? 0)
    const lr = Number(p.lr ?? 0)
    const pc = Number(p.percent ?? 0)

    if (st > 0) { steps.push(st); lastStep = st }
    if (ls > 0) losses.push(ls)
    if (lr > 0) lrs.push(lr)
    if (pc > 0) { percents.push(pc); progress = pc }
    if (tt > 0) totalSteps = tt
  }

  const lastLoss = losses.length ? losses[losses.length - 1] : 0
  const bestLoss = losses.length ? Math.min(...losses) : 0

  return {
    steps, losses, lrs, percents,
    lastLoss, bestLoss, lastStep, totalSteps, progress,
  }
}
