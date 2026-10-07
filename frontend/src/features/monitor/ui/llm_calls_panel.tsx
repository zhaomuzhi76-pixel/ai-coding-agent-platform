import { useCallback, useEffect, useState } from "react"

import {
  providersApi, type CallRecord,
} from "../../../core/api/providers_api"
import type { CostStats, BucketStats } from "../../../core/contracts/cost"
import {
  Badge, EmptyState, Sparkline,
} from "../../../app/ui/industrial"

import { ModelStatsTable } from "./model_stats_table"
import {
  TimeSelector, rangeToDays, type TimeRange,
} from "./time_selector"

import "./llm_calls_panel.css"

function timeHHMM(ts: number): string {
  const d = new Date(ts * 1000)
  return [d.getHours(), d.getMinutes(), d.getSeconds()]
    .map((n) => String(n).padStart(2, "0"))
    .join(":")
}

import { renderLlmCallsPanel } from "./_llm_calls_panel_parts/render";
import { INTERVALS } from "../../../core/config/intervals"

function fmtCost(v: number): string {
  if (v === 0) return "$0"
  if (v < 0.0001) return `$${v.toExponential(2)}`
  return `$${v.toFixed(4)}`
}

export function LlmCallsPanel() {
  const [range, setRange] = useState<TimeRange>("7d")
  const [stats, setStats] = useState<CostStats | null>(null)
  const [records, setRecords] = useState<CallRecord[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const days = rangeToDays(range)
      const [s, recent] = await Promise.all([
        providersApi.costStats(days),
        providersApi.costRecent(50),
      ])
      setStats(s as unknown as CostStats)
      setRecords(recent.records)
      setError(null)
    } catch (err) {
      setError(String(err))
    }
  }, [range])

  useEffect(() => {
    void load()
    const id = window.setInterval(() => { void load() }, INTERVALS.fast)
    return () => window.clearInterval(id)
  }, [load])

  const total = stats?.total
  const online = stats?.online
  const local = stats?.local
  const onlineCalls = online?.calls ?? 0
  const localCalls = local?.calls ?? 0
  const sumCalls = onlineCalls + localCalls

  const trend = records.slice(-12).map((r) => r.latency_ms)

  return renderLlmCallsPanel({ error, fmtCost, local, localCalls, online, onlineCalls, range, records, setRange, stats, sumCalls, timeHHMM, total, trend });
}
