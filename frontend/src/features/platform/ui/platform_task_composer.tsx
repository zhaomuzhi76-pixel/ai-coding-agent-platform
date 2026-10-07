import { useState } from "react"

export function PlatformTaskComposer(props: {
  disabled: boolean
  defaultFiles: string
  onSubmit: (task: string, files: string[]) => void
}) {
  const [task, setTask] = useState("")
  const [files, setFiles] = useState(props.defaultFiles)

  const submit = () => {
    const trimmed = task.trim()
    if (!trimmed) return
    const list = files
      .split(",")
      .map((f) => f.trim())
      .filter(Boolean)
    if (list.length === 0) return
    props.onSubmit(trimmed, list)
    setTask("")
  }

  return (
    <div className="task-composer">
      <textarea
        placeholder="描述本次改动（如：给 crop.py 增加 SEED_RATE 常量）"
        value={task}
        disabled={props.disabled}
        onChange={(e) => setTask(e.target.value)}
      />
      <input
        placeholder="目标文件（逗号分隔，相对路径）"
        value={files}
        disabled={props.disabled}
        onChange={(e) => setFiles(e.target.value)}
      />
      <div className="task-composer__actions">
        <button
          className="btn btn--primary"
          disabled={props.disabled || !task.trim()}
          onClick={submit}
        >
          生成提案
        </button>
      </div>
    </div>
  )
}
