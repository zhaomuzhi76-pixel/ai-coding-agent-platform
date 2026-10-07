/** 微调管理主面板（Dify 风格 + 送 RAG） */
import { useCallback, useEffect, useState } from "react"
import { JobCard, type JobItem } from "./JobCard"
import { AdapterCard, type AdapterItem } from "./AdapterCard"
import { NewJobModal, type NewJobPayload } from "./NewJobModal"

async function _j<T>(p: string, init?: RequestInit): Promise<T> {
  const r = await fetch(p, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json()
}

export function FinetuneDashboard() {
  const [jobs, setJobs] = useState<JobItem[]>([])
  const [adapters, setAdapters] = useState<AdapterItem[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [modal, setModal] = useState(false)
  const [err, setErr] = useState("")
  const [tab, setTab] = useState<"jobs" | "adapters">("jobs")

  const refresh = useCallback(async () => {
    try {
      const [j, a, s] = await Promise.all([
        _j<any>("/api/finetune/jobs?limit=100"),
        _j<any>("/api/finetune/adapters?limit=100"),
        _j<any>("/api/finetune/summary"),
      ])
      setJobs(j?.data?.jobs ?? j?.jobs ?? [])
      setAdapters(a?.data?.adapters ?? a?.adapters ?? [])
      setSummary(s?.data ?? s)
      setErr("")
    } catch (e) {
      setErr(String(e))
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(refresh, 5000)
    return () => window.clearInterval(id)
  }, [refresh])

  const submit = async (p: NewJobPayload) => {
    try {
      await _j("/api/finetune/jobs", {
        method: "POST", body: JSON.stringify({
          recipe_name: p.recipe_name,
          base_model: p.base_model,
          dataset_path: p.dataset_path,
          epochs: p.epochs,
        }),
      })
      setModal(false)
      await refresh()
    } catch (e) { setErr(String(e)) }
  }

  const cancel = (id: string) => {
    if (window.confirm(`停止 ${id}？`)) {
      _j(`/api/finetune/jobs/${id}/cancel`, { method: "POST" }).then(refresh)
    }
  }
  const del = (id: string) => {
    if (window.confirm(`删除 ${id}？`)) {
      _j(`/api/finetune/jobs/${id}`, { method: "DELETE" }).then(refresh)
    }
  }
  const retry = (id: string) => {
    _j(`/api/finetune/jobs/${id}/retry`, { method: "POST" })
      .then(refresh).catch(() => alert("后端未提供重试接口"))
  }
  const deploy = (id: string) => {
    _j(`/api/finetune/adapters/${id}/deploy`, { method: "POST", body: "{}" })
      .then(() => alert("部署已启动，见部署 WebSocket 日志"))
      .catch((e) => alert("部署失败: " + e))
  }
  const delAdapter = (id: string) => {
    if (window.confirm(`删除产出 ${id}？`)) {
      _j(`/api/finetune/adapters/${id}`, { method: "DELETE" }).then(refresh)
    }
  }

  const runningCount = jobs.filter((j) => j.state === "running" || j.state === "queued").length

  return (
    <div className="ft-dashboard">
      <header className="ft-topbar">
        <h2>🎛️ 微调管理</h2>
        <div className="ft-kpi">
          <span>任务 <b>{jobs.length}</b></span>
          <span>运行中 <b>{runningCount}</b></span>
          <span>产出 <b>{adapters.length}</b></span>
          {summary?.gpu && <span>GPU <b>{summary.gpu}</b></span>}
        </div>
        <button className="ft-btn-primary" onClick={() => setModal(true)}>
          + 新建微调
        </button>
      </header>

      {err && <div className="ft-err">加载失败: {err}</div>}

      <div className="ft-tabs">
        <button className={tab === "jobs" ? "active" : ""}
                onClick={() => setTab("jobs")}>
          任务列表 ({jobs.length})
        </button>
        <button className={tab === "adapters" ? "active" : ""}
                onClick={() => setTab("adapters")}>
          产出模型 ({adapters.length})
        </button>
      </div>

      {tab === "jobs" && (
        <div className="ft-grid">
          {jobs.length === 0 ? (
            <div className="ft-empty">暂无微调任务</div>
          ) : (
            jobs.map((j) => (
              <JobCard key={j.job_id} job={j}
                       onDetail={() => {}}
                       onCancel={cancel}
                       onDelete={del}
                       onRetry={retry} />
            ))
          )}
        </div>
      )}

      {tab === "adapters" && (
        <div className="ft-grid">
          {adapters.length === 0 ? (
            <div className="ft-empty">暂无微调产出</div>
          ) : (
            adapters.map((a) => (
              <AdapterCard key={a.adapter_id} adapter={a}
                           onDeploy={deploy} onDelete={delAdapter} />
            ))
          )}
        </div>
      )}

      <NewJobModal open={modal} onClose={() => setModal(false)} onSubmit={submit} />
    </div>
  )
}

export default FinetuneDashboard
