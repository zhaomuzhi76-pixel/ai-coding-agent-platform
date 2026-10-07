/** RuleRow —— 单条项目规则的展示 / 内联编辑行（独立组件，无循环依赖） */
import {
  SCOPE_LABEL,
  type Preference,
} from "../../../../core/api/memory_api"

export const KIND_LABEL: Record<string, string> = {
  rule_param: "参数",
  code_style: "代码",
  workflow: "流程",
  tech_stack: "技术栈",
  language: "语言",
  style: "风格",
  dislike: "避免",
  other: "其它",
}

export function RuleRow(props: {
  r: Preference
  editing: boolean
  editVal: string
  busy: boolean
  onEditStart: () => void
  onEditChange: (v: string) => void
  onEditSave: () => void
  onEditCancel: () => void
  onDelete: () => void
}) {
  const { r, editing, editVal, busy } = props
  const scopeTag = SCOPE_LABEL[r.scope] || r.scope
  return (
    <div className="prp__row">
      <span className={`prp__scope prp__scope--${r.scope}`}>{scopeTag}</span>
      <span className="prp__kind">{KIND_LABEL[r.kind] || r.kind}</span>
      <span className="prp__key">{r.key}</span>
      {editing ? (
        <>
          <input className="prp__edit" value={editVal} autoFocus
                 onChange={(e) => props.onEditChange(e.target.value)} />
          <button type="button" className="prp__btn prp__btn--primary"
                  disabled={busy}
                  onClick={props.onEditSave}>保存</button>
          <button type="button" className="prp__btn"
                  onClick={props.onEditCancel}>取消</button>
        </>
      ) : (
        <>
          <span className="prp__val">{r.value}</span>
          <button type="button" className="prp__btn"
                  onClick={props.onEditStart}>改</button>
          <button type="button" className="prp__btn prp__btn--danger"
                  disabled={busy}
                  onClick={props.onDelete}>删</button>
        </>
      )}
    </div>
  )
}
