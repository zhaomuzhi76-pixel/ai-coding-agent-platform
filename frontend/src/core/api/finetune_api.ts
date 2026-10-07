import { request } from "../http/http_client"
import type {
  FinetuneRun,
  FinetuneSummary,
  AdapterSpec,
  DatasetSpec,
  DatasetUpdatePayload,
  EnvReport,
  DatasetStats,
  DatasetValidationReport,
  DeployPlan,
  DeployResult,
  MountedAdapter,
  JobEvent,
  JobRecord,
  RecipeDetail,
  RecipeInfo,
  SubmitJobPayload,
} from "../contracts/finetune"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const payload = await request<Envelope<T>>(path, init)
  if (!payload.ok || payload.data === undefined) {
    throw new Error(
      payload.error
        ? `${payload.error.code}: ${payload.error.message}`
        : "unknown error",
    )
  }
  return payload.data
}

export const finetuneApi = {
  summary(): Promise<FinetuneSummary> {
    return call("/finetune/summary")
  },
  recipes(): Promise<{ recipes: RecipeInfo[]; count: number }> {
    return call("/finetune/recipes")
  },
  recipe(name: string): Promise<RecipeDetail> {
    return call(`/finetune/recipes/${encodeURIComponent(name)}`)
  },
  runs(): Promise<{ runs: FinetuneRun[]; count: number }> {
    return call("/finetune/runs")
  },
  // ─── 任务管理（L2）───
  submitJob(payload: SubmitJobPayload): Promise<JobRecord> {
    return call("/finetune/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  listJobs(state = "", limit = 50): Promise<{ jobs: JobRecord[]; count: number }> {
    const qs = new URLSearchParams()
    if (state) qs.set("state", state)
    qs.set("limit", String(limit))
    return call(`/finetune/jobs?${qs.toString()}`)
  },
  getJob(jobId: string): Promise<JobRecord> {
    return call(`/finetune/jobs/${encodeURIComponent(jobId)}`)
  },
  getJobEvents(jobId: string, limit = 500): Promise<{ events: JobEvent[]; count: number }> {
    return call(`/finetune/jobs/${encodeURIComponent(jobId)}/events?limit=${limit}`)
  },
  cancelJob(jobId: string): Promise<{ cancelled: boolean; job_id: string }> {
    return call(`/finetune/jobs/${encodeURIComponent(jobId)}/cancel`, {
      method: "POST",
    })
  },
  deleteJob(jobId: string): Promise<{ deleted: boolean; job_id: string }> {
    return call(`/finetune/jobs/${encodeURIComponent(jobId)}`, {
      method: "DELETE",
    })
  },
  jobStates(): Promise<{ states: string[] }> {
    return call("/finetune/job-states")
  },
  // ─── 数据集（D4-L2）───
  uploadDataset(payload: {
    name: string
    content: string
    description?: string
    tags?: string[]
  }): Promise<DatasetSpec> {
    return call("/finetune/datasets", {
      method: "POST",
      body: JSON.stringify(payload),
    })
  },
  validateDataset(content: string): Promise<DatasetValidationReport> {
    return call("/finetune/datasets/validate", {
      method: "POST",
      body: JSON.stringify({ content }),
    })
  },
  listDatasets(limit = 100): Promise<{ datasets: DatasetSpec[]; count: number }> {
    return call(`/finetune/datasets?limit=${limit}`)
  },
  getDataset(datasetId: string): Promise<DatasetSpec> {
    return call(`/finetune/datasets/${encodeURIComponent(datasetId)}`)
  },
  deleteDataset(datasetId: string): Promise<{ deleted: boolean; dataset_id: string }> {
    return call(`/finetune/datasets/${encodeURIComponent(datasetId)}`, {
      method: "DELETE",
    })
  },
  updateDataset(datasetId: string, payload: DatasetUpdatePayload): Promise<DatasetSpec> {
    return call(`/finetune/datasets/${encodeURIComponent(datasetId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    })
  },
  datasetStats(): Promise<DatasetStats> {
    return call("/finetune/datasets/stats/overview")
  },
  downloadDataset(datasetId: string): Promise<{ dataset_id: string; content: string }> {
    return call(`/finetune/datasets/${encodeURIComponent(datasetId)}/download`)
  },
  // ─── Adapter 部署（D5-L2）───
  listAdapters(limit = 100): Promise<{ adapters: AdapterSpec[]; count: number }> {
    return call(`/finetune/adapters?limit=${limit}`)
  },
  scanAdapters(): Promise<{ scanned: number; adapters: AdapterSpec[] }> {
    return call("/finetune/adapters/scan", { method: "POST" })
  },
  getAdapter(adapterId: string): Promise<AdapterSpec> {
    return call(`/finetune/adapters/${encodeURIComponent(adapterId)}`)
  },
  buildAdapterPlan(adapterId: string): Promise<DeployPlan> {
    return call(`/finetune/adapters/${encodeURIComponent(adapterId)}/plan`)
  },
  deployAdapter(adapterId: string): Promise<DeployResult> {
    return call(`/finetune/adapters/${encodeURIComponent(adapterId)}/deploy`, {
      method: "POST",
    })
  },
  mountAdapter(adapterId: string): Promise<MountedAdapter> {
    return call(`/finetune/adapters/${encodeURIComponent(adapterId)}/mount`, {
      method: "POST",
    })
  },
  listMounted(): Promise<{ mounted: MountedAdapter[]; count: number }> {
    return call("/finetune/adapters/mounted")
  },
  deleteAdapter(adapterId: string): Promise<{ deleted: boolean; adapter_id: string }> {
    return call(`/finetune/adapters/${encodeURIComponent(adapterId)}`, {
      method: "DELETE",
    })
  },
  // ─── 环境检测（D）───
  envReport(): Promise<EnvReport> {
    return call("/finetune/env")
  },
}
