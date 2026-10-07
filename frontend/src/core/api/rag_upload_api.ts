/** RAG 文件上传 API。职责：multipart 上传，唯一网络出口。
 * 不做 UI、不持状态、不解析文件。 */
import { apiBase } from "../config/runtime"
const BASE = `${apiBase()}/rag/ingest`

interface Envelope<T> { ok: boolean; data?: T; error?: { code: string; message: string } }

export interface JobProgress {
  phase: string
  current: number
  total: number
  indexed: number
  percent: number
  message: string
}

export interface IngestJob {
  job_id: string
  filename: string
  kb: string
  lang: string
  size_bytes: number
  status: "pending" | "running" | "pending_review" | "done" | "failed" | "cancelled"
  progress: JobProgress
  created_at: number
  started_at: number
  finished_at: number
  elapsed_ms: number
  error: string
  origin_hash: string
  chunks_indexed: number
  meta: Record<string, unknown>
}

export interface OriginInfo {
  hash: string
  size: number
  ext: string
}

export interface AsyncUploadResult {
  job_id: string
  filename: string
  kb: string
  size_bytes: number
  status: string
  poll_url: string
}

export interface UploadResult {
  filename: string
  kb: string
  total: number
  succeeded: number
  failed: number
  chunks_indexed: number
  errors: string[]
  elapsed_ms: number
  origin?: OriginInfo
}

/** 原件下载 URL。 */
export function originUrl(hash: string): string {
  return `${BASE.replace("/ingest", "")}/origin/${encodeURIComponent(hash)}`
}

export interface PreviewResult {
  path: string
  title: string
  source_type: string
  page_count: number
  total_text_chars: number
  file_size: number
  preview: Array<{ page_no: number; section: string; chars: number; text: string }>
}

async function parseResp<T>(r: Response): Promise<T> {
  const payload = (await r.json()) as Envelope<T>
  if (!payload.ok || payload.data === undefined) {
    throw new Error(payload.error
      ? `${payload.error.code}: ${payload.error.message}`
      : "unknown error")
  }
  return payload.data
}

export const ragUploadApi = {
  async uploadFile(file: File, opts: {
    kb?: string; dry_run?: boolean; lang?: string
  } = {}): Promise<UploadResult> {
    const fd = new FormData()
    fd.append("file", file)
    fd.append("kb", opts.kb ?? "general")
    fd.append("batch_size", "64")
    fd.append("dry_run", String(opts.dry_run ?? false))
    if (opts.lang) fd.append("lang", opts.lang)
    const r = await fetch(`${BASE}/upload`, { method: "POST", body: fd })
    return parseResp<UploadResult>(r)
  },
  /** 上传返回 job_id（异步）。 */
  async uploadFileAsync(file: File, opts: {
    kb?: string; lang?: string; dry_run?: boolean
  } = {}): Promise<AsyncUploadResult> {
    const fd = new FormData()
    fd.append("file", file)
    fd.append("kb", opts.kb ?? "general")
    fd.append("lang", opts.lang ?? "")
    fd.append("dry_run", String(opts.dry_run ?? false))
    const r = await fetch(`${BASE}/upload`, { method: "POST", body: fd })
    return parseResp<AsyncUploadResult>(r)
  },
  /** 查询单个 job。 */
  async getJob(jobId: string): Promise<IngestJob> {
    // [SAFE_RESPONSE] 容错：后端阻塞时可能返回空/非 JSON
    const r = await fetch(`${BASE}/jobs/${encodeURIComponent(jobId)}`)
    const text = await r.text()
    if (!text || !text.trim()) {
      throw new Error("EMPTY_RESPONSE")  // 上层 catch 会跳过
    }
    try {
      const payload = JSON.parse(text)
      // [FIX_ENVELOPE] 后端返回 {"ok":true,"data":{...}}，需解包
      if (payload && payload.ok === true && payload.data) {
        return payload.data as IngestJob
      }
      if (payload && payload.ok === false && payload.error) {
        throw new Error(`${payload.error.code}: ${payload.error.message}`)
      }
      // 兼容：老格式直接返回裸对象
      if (payload && payload.job_id) return payload as IngestJob
      throw new Error("UNEXPECTED_PAYLOAD")
    } catch (e) {
      throw new Error(`INVALID_JSON: ${e}`)
    }
  },
  /** 列出最近 jobs。 */
  async listJobs(limit = 20): Promise<{ total: number; jobs: IngestJob[] }> {
    const r = await fetch(`${BASE}/jobs?limit=${limit}`)
    return parseResp<{ total: number; jobs: IngestJob[] }>(r)
  },
  /** 取消 job。 */
  async cancelJob(jobId: string): Promise<{ cancelled: boolean; job_id: string }> {
    const r = await fetch(`${BASE}/jobs/${encodeURIComponent(jobId)}/cancel`,
                          { method: "POST" })
    return parseResp<{ cancelled: boolean; job_id: string }>(r)
  },
  /** 删除单条 job。 */
  async deleteJob(jobId: string): Promise<{ deleted: boolean; job_id: string }> {
    const r = await fetch(`${BASE}/jobs/${encodeURIComponent(jobId)}`,
                          { method: "DELETE" })
    return parseResp<{ deleted: boolean; job_id: string }>(r)
  },
  /** 拉某个 job 的 chunks（分页）。 */
  async getJobChunks(jobId: string, offset = 0, limit = 100): Promise<{
    total: number; offset: number; limit: number;
    chunks: Array<{ chunk_id: string; text: string;
                    metadata: Record<string, unknown> }>;
    note?: string;
  }> {
    const r = await fetch(
      `${BASE}/jobs/${encodeURIComponent(jobId)}/chunks?offset=${offset}&limit=${limit}`)
    return parseResp(r)
  },
  /** 清空所有 job 记录。 */
  async clearJobs(): Promise<{ cleared: number }> {
    const r = await fetch(`${BASE}/jobs`, { method: "DELETE" })
    return parseResp<{ cleared: number }>(r)
  },
  async preview(path: string, kb = "general"): Promise<PreviewResult> {
    const r = await fetch(`${BASE}/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, kb }),
    })
    return parseResp<PreviewResult>(r)
  },
}
