/** 项目规则面板 —— Agent 输入框下方，用户可看/改/删已学规则。
 *
 * 数据源：memoryApi（sqlite 持久化）
 * 作用域：按当前 workspace 过滤（global + 匹配 project/session）
 */
import { useCallback, useEffect, useMemo, useState } from "react"

import {
  memoryApi, SCOPE_LABEL,
  type Preference, type RuleScope,
} from "../../../../core/api/memory_api"

import "../project_rules_panel.css"
import { RuleRow } from "./RuleRow"


interface Props {
  workspace: string
}

// Auto-extracted render function for ProjectRulesPanel.
export interface ProjectRulesPanelRenderProps {
  busy: any
  editId: any
  editVal: any
  err: any
  load: any
  nKey: any
  nScope: any
  nVal: any
  onAdd: any
  onDelete: any
  onSaveEdit: any
  open: any
  otherRules: any
  paramCount: any
  paramRules: any
  setEditId: any
  setEditVal: any
  setNKey: any
  setNScope: any
  setNVal: any
  setOpen: any
  setShowAdd: any
  showAdd: any
  total: any
}

export function renderProjectRulesPanel(props: ProjectRulesPanelRenderProps) {
  const { busy, editId, editVal, err, load, nKey, nScope, nVal, onAdd, onDelete, onSaveEdit, open, otherRules, paramCount, paramRules, setEditId, setEditVal, setNKey, setNScope, setNVal, setOpen, setShowAdd, showAdd, total } = props;
  void busy;
  return (

      <section className="prp">
        <header
          className="prp__head"
          onClick={() => setOpen(v => !v)}
          role="button"
          tabIndex={0}
        >
          <span className="prp__arrow">{open ? "▼" : "▶"}</span>
          <span className="prp__title">项目规则</span>
          <span className="prp__count">
            {total} 条{paramCount > 0 && ` · ${paramCount} 参数`}
          </span>
          <span className="prp__spacer" />
          <button
            type="button" className="prp__btn"
            onClick={(e) => { e.stopPropagation(); void load() }}
            disabled={busy}
          >刷新</button>
          <button
            type="button" className="prp__btn"
            onClick={(e) => { e.stopPropagation(); setShowAdd(v => !v) }}
          >{showAdd ? "收起" : "+ 添加"}</button>
        </header>

        {err && <div className="prp__err">{err}</div>}

        {open && (
          <div className="prp__body">
            {showAdd && (
              <div className="prp__add">
                <input placeholder="key（如 file_size_max_230.max_lines）"
                       value={nKey}
                       onChange={(e) => setNKey(e.target.value)} />
                <input placeholder="value（如 200）"
                       value={nVal}
                       onChange={(e) => setNVal(e.target.value)} />
                <select value={nScope}
                        onChange={(e) => setNScope(e.target.value as RuleScope)}>
                  <option value="project">项目</option>
                  <option value="global">全局</option>
                  <option value="session">会话</option>
                </select>
                <button type="button" className="prp__btn prp__btn--primary"
                        disabled={busy}
                        onClick={() => void onAdd()}>保存</button>
              </div>
            )}

            {paramRules.length > 0 && (
              <div className="prp__group">
                <div className="prp__group-title">参数（实时生效）</div>
                {paramRules.map(r => (
                  <RuleRow key={r.id} r={r}
                           editing={editId === r.id}
                           editVal={editVal}
                           onEditStart={() => { setEditId(r.id); setEditVal(r.value) }}
                           onEditChange={setEditVal}
                           onEditSave={() => void onSaveEdit(r)}
                           onEditCancel={() => setEditId(null)}
                           onDelete={() => void onDelete(r.id)}
                           busy={busy} />
                ))}
              </div>
            )}

            {otherRules.length > 0 && (
              <div className="prp__group">
                <div className="prp__group-title">偏好</div>
                {otherRules.slice(0, 30).map(r => (
                  <RuleRow key={r.id} r={r}
                           editing={false}
                           editVal=""
                           onEditStart={() => {}}
                           onEditChange={() => {}}
                           onEditSave={() => {}}
                           onEditCancel={() => {}}
                           onDelete={() => void onDelete(r.id)}
                           busy={busy} />
                ))}
                {otherRules.length > 30 && (
                  <div className="prp__more">… 还有 {otherRules.length - 30} 条</div>
                )}
              </div>
            )}

            {total === 0 && (
              <div className="prp__empty">
                暂无规则。在 Agent 输入框说"单文件改为200行"即可自动学。
              </div>
            )}
          </div>
        )}
      </section>
  );
}
