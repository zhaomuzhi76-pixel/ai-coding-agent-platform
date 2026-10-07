/**
 * DatasetPanel: 数据集管理面板（D4-L2）。
 *
 * 职责：
 *   - 上传 JSONL 文件（拖拽 / 点选）
 *   - 上传前预校验（显示样本数 / 错误 / 预览）
 *   - 确认后上传
 *   - 列表 + 删除 + 下载
 */
import { useCallback, useEffect, useRef, useState } from "react"

import { finetuneApi } from "../../../core/api/finetune_api"
import type {
  DatasetSpec,
  DatasetStats,
  DatasetValidationReport,
} from "../../../core/contracts/finetune"
import { Badge, EmptyState } from "../../../app/ui/industrial"

import { renderDatasetPanel } from "./_dataset_panel_parts/render";
import { INTERVALS } from "../../../core/config/intervals"



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

export function DatasetPanel() {
  const [datasets, setDatasets] = useState<DatasetSpec[]>([])
  const [stats, setStats] = useState<DatasetStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 上传
  const [uploadName, setUploadName] = useState("")
  const [uploadDesc, setUploadDesc] = useState("")
  const [fileContent, setFileContent] = useState<string>("")
  const [fileName, setFileName] = useState<string>("")
  const [report, setReport] = useState<DatasetValidationReport | null>(null)
  const [uploading, setUploading] = useState(false)
  const [editTarget, setEditTarget] = useState<DatasetSpec | null>(null)
  const [editName, setEditName] = useState("")
  const [editDesc, setEditDesc] = useState("")
  const [editTags, setEditTags] = useState("")
  const [editSaving, setEditSaving] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const loadAll = useCallback(async () => {
    try {
      const [d, s] = await Promise.all([
        finetuneApi.listDatasets(100),
        finetuneApi.datasetStats(),
      ])
      setDatasets(d.datasets)
      setStats(s)
      setError(null)
    } catch (e) { setError(String(e)) }
  }, [])

  useEffect(() => { void loadAll() }, [loadAll])

  // 选择文件 → 读文本 → 预校验
  const handlePickFile = async (f: File) => {
    setError(null)
    setReport(null)
    setFileName(f.name)
    if (!uploadName) setUploadName(f.name.replace(/\.jsonl?$/i, ""))
    try {
      const text = await f.text()
      setFileContent(text)
      const rep = await finetuneApi.validateDataset(text)
      setReport(rep)
    } catch (e) { setError(String(e)) }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0]
    if (f) void handlePickFile(f)
  }

  const handleSubmit = async () => {
    if (!uploadName.trim()) { setError("数据集名称必填"); return }
    if (!fileContent) { setError("请选择 JSONL 文件"); return }
    if (report && !report.ok) {
      setError("预校验未通过，请修正后重试"); return
    }
    setError(null); setUploading(true)
    try {
      await finetuneApi.uploadDataset({
        name: uploadName.trim(),
        content: fileContent,
        description: uploadDesc,
      })
      // 清空表单
      setUploadName(""); setUploadDesc(""); setFileContent("")
      setFileName(""); setReport(null)
      if (fileInputRef.current) fileInputRef.current.value = ""
      await loadAll()
    } catch (e) { setError(String(e)) }
    finally { setUploading(false) }
  }

  const handleDelete = async (did: string) => {
    if (!window.confirm(`确认删除数据集 ${did}？`)) return
    try { await finetuneApi.deleteDataset(did); await loadAll() }
    catch (e) { setError(String(e)) }
  }

  const handleDownload = async (d: DatasetSpec) => {
    try {
      const resp = await finetuneApi.downloadDataset(d.dataset_id)
      const blob = new Blob([resp.content], { type: "application/jsonl;charset=utf-8" })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${d.name || d.dataset_id}.jsonl`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(url), INTERVALS.objectUrlRevoke)
    } catch (e) {
      setError(String(e))
    }
  }

  const handleEditOpen = (d: DatasetSpec) => {
    setEditTarget(d)
    setEditName(d.name)
    setEditDesc(d.description || "")
    setEditTags((d.tags || []).join(", "))
  }

  const handleEditSave = async () => {
    if (!editTarget) return
    if (!editName.trim()) { setError("名称必填"); return }
    setEditSaving(true)
    try {
      const tags = editTags.split(",").map((t) => t.trim()).filter(Boolean)
      await finetuneApi.updateDataset(editTarget.dataset_id, {
        name: editName.trim(),
        description: editDesc,
        tags,
      })
      setEditTarget(null)
      await loadAll()
    } catch (e) { setError(String(e)) }
    finally { setEditSaving(false) }
  }

    return renderDatasetPanel({ datasets, stats, error, uploadName, setUploadName, uploadDesc, setUploadDesc, fileContent, fileName, report, uploading, editTarget, setEditTarget, editName, setEditName, editDesc, setEditDesc, editTags, setEditTags, editSaving, fileInputRef, handlePickFile, handleDrop, handleSubmit, handleDelete, handleDownload, handleEditOpen, handleEditSave });

}
