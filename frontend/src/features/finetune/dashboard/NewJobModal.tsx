/** 新建微调任务弹窗 */
import { useEffect, useState } from "react"

export interface NewJobPayload {
  recipe_name: string
  base_model: string
  dataset_path: string
  epochs?: number
}

interface Recipe { name: string; description: string }
interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (p: NewJobPayload) => void
}

const BASES = [
  "Qwen/Qwen2.5-0.5B-Instruct",
  "Qwen/Qwen2.5-1.5B-Instruct",
  "Qwen/Qwen2.5-7B-Instruct",
  "Qwen/Qwen2.5-Coder-7B-Instruct",
]

export function NewJobModal({ open, onClose, onSubmit }: Props) {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [datasets, setDatasets] = useState<any[]>([])
  const [form, setForm] = useState<NewJobPayload>({
    recipe_name: "lora-balanced",
    base_model: BASES[0],
    dataset_path: "",
  })

  useEffect(() => {
    if (!open) return
    fetch("/api/finetune/recipes").then((r) => r.json()).then((d) => {
      setRecipes(d?.data?.recipes ?? d?.recipes ?? [])
    }).catch(() => {})
    fetch("/api/finetune/datasets").then((r) => r.json()).then((d) => {
      setDatasets(d?.data?.datasets ?? d?.datasets ?? [])
    }).catch(() => {})
  }, [open])

  if (!open) return null
  const set = <K extends keyof NewJobPayload>(k: K, v: NewJobPayload[K]) =>
    setForm((f) => ({ ...f, [k]: v }))

  const canSave = form.recipe_name && form.base_model && form.dataset_path

  return (
    <div className="ft-modal-mask" onClick={onClose}>
      <div className="ft-modal" onClick={(e) => e.stopPropagation()}>
        <h3>新建微调任务</h3>

        <label>微调方法</label>
        <select value={form.recipe_name}
                onChange={(e) => set("recipe_name", e.target.value)}>
          {recipes.map((r) => (
            <option key={r.name} value={r.name}>{r.name} · {r.description}</option>
          ))}
        </select>

        <label>基础模型</label>
        <select value={form.base_model}
                onChange={(e) => set("base_model", e.target.value)}>
          {BASES.map((b) => <option key={b} value={b}>{b}</option>)}
        </select>

        <label>训练数据集</label>
        <select value={form.dataset_path}
                onChange={(e) => set("dataset_path", e.target.value)}>
          <option value="">— 选择数据集 —</option>
          {datasets.map((d: any) => (
            <option key={d.dataset_id || d.path} value={d.path || d.dataset_id}>
              {d.name || d.dataset_id} ({d.count || d.size || "?"} 条)
            </option>
          ))}
        </select>

        <div className="ft-modal-actions">
          <button onClick={onClose}>取消</button>
          <button className="primary" disabled={!canSave}
                  onClick={() => onSubmit(form)}>开始训练</button>
        </div>
      </div>
    </div>
  )
}

export default NewJobModal
