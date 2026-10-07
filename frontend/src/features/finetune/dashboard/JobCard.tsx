/** 微调任务卡片 */
import { Badge } from "../../../app/ui/industrial"

export interface JobItem {
  job_id: string
  state?: string
  spec?: { recipe_name?: string; base_model?: string; dataset_path?: string }
  progress?: number
  loss?: number
  error?: string
  created_at?: number
}

const STATE_TONE: Record<string, "success" | "muted" | "danger" | "info"> = {
  done: "success", running: "info", queued: "muted",
  failed: "danger", cancelled: "muted", pending: "muted",
}

interface Props {
  job: JobItem
  onDetail: (id: string) => void
  onCancel: (id: string) => void
  onDelete: (id: string) => void
  onRetry: (id: string) => void
}

export function JobCard({ job, onDetail, onCancel, onDelete, onRetry }: Props) {
  const st = job.state || "pending"
  const running = st === "running" || st === "queued"
  const failed = st === "failed"
  const recipe = job.spec?.recipe_name || "?"
  const base = job.spec?.base_model || "?"
  const shortBase = base.split("/").pop() || base

  return (
    <div className={`ft-job-card ft-job-${st}`}>
      <div className="ft-job-head">
        <span className="ft-job-id">{job.job_id.slice(0, 16)}</span>
        <Badge tone={STATE_TONE[st] ?? "muted"}>{st}</Badge>
      </div>
      <div className="ft-job-meta">
        <span>🍳 {recipe}</span>
        <span>🧠 {shortBase}</span>
      </div>
      {running && job.progress != null && (
        <div className="ft-job-progress">
          <div className="ft-job-progress-bar"
               style={{ width: `${Math.min(100, job.progress)}%` }} />
          <span className="ft-job-progress-text">{Math.round(job.progress)}%</span>
        </div>
      )}
      {job.loss != null && (
        <div className="ft-job-loss">loss: {Number(job.loss).toFixed(4)}</div>
      )}
      {failed && job.error && (
        <div className="ft-job-error">{job.error.slice(0, 120)}</div>
      )}
      <div className="ft-job-actions">
        <button onClick={() => onDetail(job.job_id)}>详情</button>
        {running && <button className="danger" onClick={() => onCancel(job.job_id)}>停止</button>}
        {failed && <button onClick={() => onRetry(job.job_id)}>重试</button>}
        {!running && <button className="danger" onClick={() => onDelete(job.job_id)}>删除</button>}
      </div>
    </div>
  )
}

export default JobCard
