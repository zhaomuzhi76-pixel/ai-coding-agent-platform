// [QUEUED_UI]
import { Badge } from "../../../app/ui/industrial"

interface Progress {
  phase: string
  current: number
  total: number
  percent: number
}
interface Props {
  filename: string
  sizeBytes: number
  progress?: Progress
  elapsedMs: number
  status: string
  chunks: number
  error?: string
  /** 生成中：取消任务（清草稿） */
  onCancel?: () => void
  /** 已完成：删除向量数据 */
  onDeleteVectors?: () => void
  /** 从 UI 移除卡片（不动后端） */
  onClear?: () => void
  onDetail?: () => void
}

const PHASE_LABEL: Record<string, string> = {
  saving: "保存原件", queued: "排队中", parsing: "解析文本", ocr: "OCR 识别",
  chunking: "切分文档", embedding: "生成向量", indexing: "写入向量库",
  finalizing: "切分文档", pending_review: "准备向量化",
  done: "完成", failed: "失败", pending: "排队中", running: "处理中",
  error: "错误", cancelled: "已取消",
}
const TONE: Record<string, "success" | "info" | "danger" | "warning" | "muted"> = {
  done: "success", running: "info", pending: "muted",
  failed: "danger", error: "danger", cancelled: "muted",
  pending_review: "info",
}
function fmt(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const m = Math.floor(ms / 60000)
  const s = Math.round((ms % 60000) / 1000)
  return `${m}分${s}秒`
}

export function UploadProgressDetail(p: Props) {
  const prog = p.progress
  const cur = prog?.current ?? 0
  const total = prog?.total ?? 0
  const pct = (prog?.percent ?? 0) * 100   // [0-1] → [0-100]
  const perUnit = cur > 0 ? p.elapsedMs / cur : 0
  const remaining = Math.max(0, total - cur)
  const eta = perUnit > 0 && remaining > 0 ? perUnit * remaining : 0
  const isDone = p.status === "done"
  const isFailed = ["failed", "error"].includes(p.status)
  const isCancelled = p.status === "cancelled"
  const isActive = ["pending", "running", "pending_review"].includes(p.status)

  return (
    <div className="ind-card" style={{ padding: 12, marginBottom: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>📄 {p.filename}</span>
        <span style={{ fontSize: 11, color: "var(--text-soft)" }}>
          {(p.sizeBytes / 1024 / 1024).toFixed(2)} MB
        </span>
        <Badge tone={TONE[p.status] ?? "muted"}>{PHASE_LABEL[p.status] ?? p.status}</Badge>
        <span style={{ fontSize: 14, fontWeight: 700,
                       color: isDone ? "#22c55e" : isFailed ? "#ef4444"
                             : isCancelled ? "#6b7280" : "#f59e0b",
                       fontFamily: "ui-monospace, monospace" }}>
          {isDone ? "100.0%" : `${pct.toFixed(1)}%`}
        </span>
      </div>

      <div style={{ height: 6, background: "#2a2a2e", borderRadius: 3,
                    overflow: "hidden", marginBottom: 10 }}>
        <div style={{ height: "100%", width: `${isDone ? 100 : pct}%`,
                      background: isDone
                        ? "linear-gradient(90deg,#22c55e,#16a34a)"
                        : isFailed ? "#ef4444"
                        : "linear-gradient(90deg,#2563eb,#22c55e)",
                      transition: "width .3s" }} />
      </div>

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap",
                    fontSize: 12, color: "var(--text-soft)", marginBottom: 8 }}>
        {prog?.phase && !isDone && <span>阶段 <b style={{ color: "var(--text)" }}>
          {PHASE_LABEL[prog.phase] ?? prog.phase}</b></span>}
        {total > 0 && (
          <span>进度 <b style={{ color: "var(--text)" }}>{cur}/{total}</b>
            {remaining > 0 && ` · 剩 ${remaining}`}
          </span>
        )}
        {perUnit > 0 && !isDone && <span>单位耗时 <b style={{ color: "var(--text)" }}>
          {fmt(perUnit)}</b></span>}
        {eta > 0 && !isDone && <span>预计还需 <b style={{ color: "#f59e0b" }}>
          ~{fmt(eta)}</b></span>}
        {p.elapsedMs > 0 && <span>{isDone ? "总耗时" : "已耗时"} <b style={{ color: "var(--text)" }}>
          {fmt(p.elapsedMs)}</b></span>}
        {p.chunks > 0 && <span>已入库 <b style={{ color: "#22c55e" }}>
          {p.chunks} 块向量</b></span>}
      </div>

      {isDone && (
        <div style={{ padding: "6px 10px", background: "rgba(79,214,154,.08)",
                      border: "1px solid rgba(79,214,154,.3)",
                      borderRadius: 4, fontSize: 12, color: "#4fd69a" }}>
          ✅ 已完成并入库 {p.chunks} 块向量，可去【📦 已入库】tab 查看
        </div>
      )}
      {isCancelled && (
        <div style={{ padding: "6px 10px", background: "rgba(107,114,128,.1)",
                      borderRadius: 4, fontSize: 12, color: "#9ca3af" }}>
          ⊘ 已取消，临时文件已清理
        </div>
      )}
      {p.error && (
        <div style={{ padding: "6px 10px", background: "rgba(239,68,68,.1)",
                      border: "1px solid rgba(239,68,68,.3)", borderRadius: 4,
                      fontSize: 11, color: "#fca5a5", marginTop: 8 }}>❌ {p.error}</div>
      )}

      {/* 按钮区（按状态显示对应按钮） */}
      <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
        {p.status === "pending" && (
        <div style={{
          padding: "6px 10px", background: "rgba(148,163,184,.08)",
          border: "1px solid rgba(148,163,184,.3)",
          borderRadius: 4, fontSize: 12, color: "#94a3b8",
          marginBottom: 6,
        }}>
          ⏳ 排队中（等待处理）
        </div>
      )}
      {isActive && p.onCancel && (
          <button className="ind-btn"
                  style={{ borderColor: "#7f1d1d", color: "#fca5a5" }}
                  onClick={() => {
                    if (window.confirm("取消本次处理？临时草稿会一并清理。"))
                      p.onCancel!()
                  }}>
            ⏹ 取消
          </button>
        )}
        {isDone && p.onDeleteVectors && (
          <button className="ind-btn"
                  style={{ borderColor: "#7f1d1d", color: "#fca5a5" }}
                  onClick={() => {
                    if (window.confirm(
                      `从向量库删除《${p.filename}》的 ${p.chunks} 块向量？此操作不可逆。`))
                      p.onDeleteVectors!()
                  }}>
            🗑 删除向量数据
          </button>
        )}
        {p.onDetail && (
          <button className="ind-btn" onClick={() => {
            console.log("[DIAG] 点击【详情】按钮, 有 onDetail 回调")
            p.onDetail!()
          }}>详情</button>
        )}
        {(isDone || isFailed || isCancelled) && p.onClear && (
          <button className="ind-btn" onClick={p.onClear}>清除卡片</button>
        )}
      </div>
    </div>
  )
}
export default UploadProgressDetail
