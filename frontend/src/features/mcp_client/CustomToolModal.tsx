/** 自定义工具弹窗（Dify 风格：参数 + 代码） */
import { useEffect, useState } from "react"

export interface CustomParam {
  name: string
  type: string
  required: boolean
  description: string
}

export interface CustomToolPayload {
  name: string
  description: string
  params: CustomParam[]
  code: string
}

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (p: CustomToolPayload) => void
}

const EMPTY: CustomToolPayload = {
  name: "", description: "", params: [], code: "",
}

export function CustomToolModal({ open, onClose, onSubmit }: Props) {
  const [form, setForm] = useState<CustomToolPayload>(EMPTY)

  useEffect(() => {
    if (open) setForm(EMPTY)
  }, [open])

  if (!open) return null

  const update = <K extends keyof CustomToolPayload>(
    k: K, v: CustomToolPayload[K],
  ) => setForm((f) => ({ ...f, [k]: v }))

  const addParam = () => setForm((f) => ({
    ...f,
    params: [...f.params, {
      name: "", type: "string", required: false, description: "",
    }],
  }))

  const updateParam = (i: number, patch: Partial<CustomParam>) => {
    setForm((f) => ({
      ...f,
      params: f.params.map((p, idx) =>
        idx === i ? { ...p, ...patch } : p),
    }))
  }

  const removeParam = (i: number) => setForm((f) => ({
    ...f, params: f.params.filter((_, idx) => idx !== i),
  }))

  const canSave = form.name.trim().length > 0

  return (
    <div className="mcp-modal-mask" onClick={onClose}>
      <div className="mcp-modal" onClick={(e) => e.stopPropagation()}>
        <h3>新增自定义工具</h3>

        <label>工具名（唯一标识）</label>
        <input value={form.name}
               onChange={(e) => update("name", e.target.value)}
               placeholder="my_tool" />

        <label>描述</label>
        <textarea value={form.description}
                  onChange={(e) => update("description", e.target.value)}
                  placeholder="该工具用于..." rows={2} />

        <label>参数列表</label>
        {form.params.map((p, i) => (
          <div key={i} className="mcp-param-row">
            <input placeholder="参数名" value={p.name}
                   onChange={(e) => updateParam(i, { name: e.target.value })} />
            <select value={p.type}
                    onChange={(e) => updateParam(i, { type: e.target.value })}>
              <option value="string">string</option>
              <option value="number">number</option>
              <option value="boolean">boolean</option>
            </select>
            <label className="mcp-param-check">
              <input type="checkbox" checked={p.required}
                     onChange={(e) => updateParam(i, {
                       required: e.target.checked,
                     })} />
              必填
            </label>
            <button onClick={() => removeParam(i)}>×</button>
          </div>
        ))}
        <button className="mcp-add-param" onClick={addParam}>+ 添加参数</button>

        <label>Python 实现（可选）</label>
        <textarea value={form.code}
                  onChange={(e) => update("code", e.target.value)}
                  placeholder="def my_tool(...): ..." rows={4} />

        <div className="mcp-modal-actions">
          <button onClick={onClose}>取消</button>
          <button className="primary" disabled={!canSave}
                  onClick={() => onSubmit(form)}>保存</button>
        </div>
      </div>
    </div>
  )
}

export default CustomToolModal
