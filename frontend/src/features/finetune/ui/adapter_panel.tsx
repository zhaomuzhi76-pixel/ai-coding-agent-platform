/**
 * AdapterPanel: Adapter 部署面板（D5-L2）。
 *
 * 职责：
 *   - 扫描本地 adapter 目录
 *   - 列表 + 查看 Modelfile
 *   - 部署（ollama create）
 *   - 挂载到 providers
 *   - 删除
 */
import { useCallback, useEffect, useState } from "react"

import { finetuneApi } from "../../../core/api/finetune_api"
import type {
  AdapterSpec,
  DeployPlan,
  DeployResult,
  MountedAdapter,
  DeployStep,
} from "../../../core/contracts/finetune"
import { Badge, EmptyState } from "../../../app/ui/industrial"
import { useDeployTask } from "./use_deploy_task"

import { renderAdapterPanel } from "./_adapter_panel_parts/render";



function fmtBytes(n: number): string {
  if (n >= 1024 * 1024) return `${(n / 1024 / 1024).toFixed(2)}MB`
  if (n >= 1024) return `${(n / 1024).toFixed(1)}KB`
  return `${n}B`
}

function fmtTime(ts: number): string {
  const d = new Date(ts * 1000)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  const h = String(d.getHours()).padStart(2, "0")
  const mi = String(d.getMinutes()).padStart(2, "0")
  return `${y}-${m}-${day} ${h}:${mi}`
}

interface PlanModal {
  spec: AdapterSpec
  plan: DeployPlan
}

interface DeployModal {
  spec: AdapterSpec
  result: DeployResult
}

export function AdapterPanel() {
  const [adapters, setAdapters] = useState<AdapterSpec[]>([])
  const [mounted, setMounted] = useState<MountedAdapter[]>([])
  const [error, setError] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)
  const [deploying, setDeploying] = useState<string | null>(null)
  const [plan, setPlan] = useState<PlanModal | null>(null)
  const [deployResult, setDeployResult] = useState<DeployModal | null>(null)
  const { run: runDeployAsync } = useDeployTask()

  const loadAll = useCallback(async () => {
    try {
      const [a, m] = await Promise.all([
        finetuneApi.listAdapters(100),
        finetuneApi.listMounted(),
      ])
      setAdapters(a.adapters)
      setMounted(m.mounted)
      setError(null)
    } catch (e) { setError(String(e)) }
  }, [])

  useEffect(() => { void loadAll() }, [loadAll])

  const handleScan = async () => {
    setScanning(true); setError(null)
    try {
      const r = await finetuneApi.scanAdapters()
      setError(`扫描完成：发现 ${r.scanned} 个 adapter`)
      await loadAll()
    } catch (e) { setError(String(e)) }
    finally { setScanning(false) }
  }

  const handlePlan = async (a: AdapterSpec) => {
    try {
      const p = await finetuneApi.buildAdapterPlan(a.adapter_id)
      setPlan({ spec: a, plan: p })
    } catch (e) { setError(String(e)) }
  }

  const handleDeploy = async (a: AdapterSpec) => {
    if (!window.confirm(`确认部署 ${a.name}？\n流程: merge → GGUF → ollama create（约 15~30s）`)) return
    setDeploying(a.adapter_id); setError(null)
    const spec = a
    const initial: DeployResult = {
      ok: false, adapter_id: spec.adapter_id, model_name: "",
      returncode: 0, stdout: "", stderr: "", elapsed_sec: 0, error: "",
      steps: [], log_tail: [],
    }
    setDeployResult({ spec, result: initial })
    try {
      const r = await runDeployAsync(spec.adapter_id, (partial) => {
        setDeployResult({
          spec,
          result: { ...initial, steps: partial.steps, log_tail: partial.logs },
        })
      })
      setDeployResult({ spec, result: r })
      await loadAll()
    } catch (e) { setError(String(e)) }
    finally { setDeploying(null) }
  }

  const handleMount = async (a: AdapterSpec) => {
    try {
      await finetuneApi.mountAdapter(a.adapter_id)
      await loadAll()
    } catch (e) { setError(String(e)) }
  }

  const handleDelete = async (a: AdapterSpec) => {
    if (!window.confirm(`确认从注册表删除 ${a.name}？（不删文件）`)) return
    try { await finetuneApi.deleteAdapter(a.adapter_id); await loadAll() }
    catch (e) { setError(String(e)) }
  }

  const isMounted = (aid: string) => mounted.some((m) => m.adapter_id === aid)

    return renderAdapterPanel({ adapters, mounted, error, scanning, deploying, plan, setPlan, deployResult, setDeployResult, handleScan, handlePlan, handleDeploy, handleMount, handleDelete, isMounted });

}
