/** 项目规则面板 —— Agent 输入框下方，用户可看/改/删已学规则。
 *
 * 数据源：memoryApi（sqlite 持久化）
 * 作用域：按当前 workspace 过滤（global + 匹配 project/session）
 */
import { useCallback, useEffect, useMemo, useState } from "react"

import {
  memoryApi, SCOPE_LABEL,
  type Preference, type RuleScope,
} from "../../../core/api/memory_api"

import "./project_rules_panel.css"

interface Props {
  workspace: string
}

import { RuleRow } from "./_project_rules_panel_parts/RuleRow";
import { renderProjectRulesPanel } from "./_project_rules_panel_parts/render";


export function ProjectRulesPanel({ workspace }: Props) {
  const [rules, setRules] = useState<Preference[]>([])
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState("")
  const [showAdd, setShowAdd] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [editVal, setEditVal] = useState("")
  const [nKey, setNKey] = useState("")
  const [nVal, setNVal] = useState("")
  const [nScope, setNScope] = useState<RuleScope>("project")

  const load = useCallback(async () => {
    if (!workspace) return
    try {
      const r = await memoryApi.list(0, "", workspace)
      setRules(r.preferences)
      setErr("")
    } catch (e) { setErr(String(e)) }
  }, [workspace])

  useEffect(() => { void load() }, [load])

  // 参数规则优先显示，其余按 kind 分组
  const { paramRules, otherRules } = useMemo(() => {
    const p: Preference[] = []
    const o: Preference[] = []
    for (const r of rules) {
      if (r.kind === "rule_param") p.push(r)
      else o.push(r)
    }
    return { paramRules: p, otherRules: o }
  }, [rules])

  const total = rules.length
  const paramCount = paramRules.length

  const onSaveEdit = async (r: Preference) => {
    setBusy(true)
    try {
      await memoryApi.add({
        kind: r.kind, key: r.key, value: editVal.trim(),
        confidence: r.confidence, scope: r.scope, workspace: r.workspace,
      })
      setEditId(null); await load()
    } catch (e) { setErr(String(e)) } finally { setBusy(false) }
  }

  const onDelete = async (id: number) => {
    setBusy(true)
    try { await memoryApi.remove(id); await load() }
    catch (e) { setErr(String(e)) } finally { setBusy(false) }
  }

  const onAdd = async () => {
    if (!nKey.trim() || !nVal.trim()) { setErr("key/value 必填"); return }
    setBusy(true)
    try {
      // 未带 "." 的 key 自动加 rule_param. 前缀（用户友好）
      const key = nKey.includes(".") ? nKey.trim() : nKey.trim()
      const kind = nKey.includes(".") ? "rule_param" : "code_style"
      await memoryApi.add({
        kind, key, value: nVal.trim(), confidence: 95,
        scope: nScope,
        workspace: nScope === "global" ? "" : workspace,
      })
      setNKey(""); setNVal(""); setShowAdd(false); await load()
    } catch (e) { setErr(String(e)) } finally { setBusy(false) }
  }

  if (!workspace) return null

  return renderProjectRulesPanel({ busy, editId, editVal, err, load, nKey, nScope, nVal, onAdd, onDelete, onSaveEdit, open, otherRules, paramCount, paramRules, setEditId, setEditVal, setNKey, setNScope, setNVal, setOpen, setShowAdd, showAdd, total });
}

