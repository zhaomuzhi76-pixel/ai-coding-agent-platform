import { useEffect, useState } from "react"

import {
  providersApi,
  type ProviderUpsertPayload,
  type TestResult,
} from "../../../core/api/providers_api"
import type { ProviderInfo } from "../../../core/contracts/providers"
import { Drawer } from "../../../app/ui/industrial"

import { renderProviderEditorDrawer } from "./_provider_editor_drawer_parts/render";

const TYPES = [
  "ollama",
  "openai_compatible",
  "dashscope",
  "anthropic",
  "deepseek",
  "gemini",
] as const

const EMPTY_MODEL = {
  id: "",
  display_name: "",
  context_window: 32768,
  max_output: 8192,
  supports_tool_call: true,
  supports_stream: true,
  supports_embedding: false,
  cost_input_per_1k: 0,
  cost_output_per_1k: 0,
  strengths: [] as string[],
}

export function ProviderEditorDrawer(props: {
  open: boolean
  initial?: ProviderInfo | null
  onClose: () => void
  onSaved: () => void
}) {
  const isNew = !props.initial
  const [name, setName] = useState("")
  const [type, setType] = useState<string>("ollama")
  const [displayName, setDisplayName] = useState("")
  const [baseUrl, setBaseUrl] = useState("")
  const [apiKey, setApiKey] = useState("")
  const [modelId, setModelId] = useState("")
  const [modelDisplay, setModelDisplay] = useState("")
  const [availableModels, setAvailableModels] = useState<
    Array<{ id: string; display_name: string; context_window: number }>
  >([])
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [discovering, setDiscovering] = useState(false)
  const [busy, setBusy] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [testStatus, setTestStatus] = useState<
    "idle" | "testing" | "success" | "error"
  >("idle")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!props.open) return
    const p = props.initial
    if (p) {
      setName(p.name)
      setType(p.type)
      setDisplayName(p.display_name)
      setBaseUrl(p.base_url)
      setApiKey("__KEEP__")  // 哨兵：不改 key
      setSelectedModels((p.models || []).map((m: any) => m.id).filter(Boolean))
      const m = (p.models && p.models[0]) || null
      if (m) {
        setModelId(m.id)
        setModelDisplay(m.display_name || m.id)
      }
    } else {
      setName("")
      setType("ollama")
      setDisplayName("")
      setBaseUrl("")
      setApiKey("")
      setModelId("")
      setModelDisplay("")
    }
    setTestResult(null)
    setError(null)
  }, [props.open, props.initial])

  // 关键字段变化时，清空测试结果，强制用户重新测试
  useEffect(() => {
    setTestResult(null)
    setTestStatus("idle")
  }, [baseUrl, apiKey, type, modelId, selectedModels])

  // ollama 类型：自动拉本地模型列表
  useEffect(() => {
    if (!props.open) return
    if (type !== "ollama") { setAvailableModels([]); return }
    if (!baseUrl.trim()) { setAvailableModels([]); return }
    let cancelled = false
    setDiscovering(true)
    const t = setTimeout(async () => {
      try {
        const r = await providersApi.localModels(name || "(new)", baseUrl)
        if (cancelled) return
        setAvailableModels(r.models || [])
      } catch {
        if (!cancelled) setAvailableModels([])
      } finally {
        if (!cancelled) setDiscovering(false)
      }
    }, 400)
    return () => clearTimeout(t)
  }, [props.open, type, baseUrl, name])

  const buildPayload = (): ProviderUpsertPayload => {
    if (!name.trim()) throw new Error("name required")
    if (!baseUrl.trim()) throw new Error("base_url required")
    const modelsFromSelection =
      type === "ollama" && selectedModels.length > 0
        ? selectedModels.map((id) => ({
            ...EMPTY_MODEL,
            id,
            display_name: id,
          }))
        : null
    if (!modelsFromSelection && !modelId.trim()) {
      throw new Error(
        type === "ollama"
          ? "至少选 1 个本地模型"
          : "at least 1 model.id required",
      )
    }
    // 清理 key 中的所有空白（用户从控制台复制经常带 \n）
    const cleanKey =
      apiKey === "__KEEP__"
        ? apiKey
        : apiKey.replace(/\s+/g, "")
    return {
      name: name.trim(),
      type,
      display_name: displayName.trim() || name.trim(),
      base_url: baseUrl.trim(),
      api_key: cleanKey,
      models: modelsFromSelection || [{
        ...EMPTY_MODEL,
        id: modelId.trim(),
        display_name: modelDisplay.trim() || modelId.trim(),
      }],
    }
  }

  const onTest = async () => {
    setError(null)
    setTestResult(null)
    setTestStatus("testing")
    try {
      const payload = buildPayload()
      const r = await providersApi.test({
        type: payload.type,
        base_url: payload.base_url,
        api_key: payload.api_key,
        models: payload.models,
      })
      setTestResult(r)
      setTestStatus(r.success ? "success" : "error")
    } catch (e) {
      setError(String(e))
      setTestStatus("error")
    }
  }

  const onSave = async () => {
    setError(null)
    if (!testResult?.success) {
      setError("请先点「测试连接」并通过，才能保存")
      return
    }
    setBusy(true)
    try {
      const payload = buildPayload()
      await providersApi.upsert(payload)
      props.onSaved()
      props.onClose()
    } catch (e) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return renderProviderEditorDrawer({ TYPES, apiKey, availableModels, baseUrl, busy, discovering, displayName, error, isNew, modelDisplay, modelId, name, onSave, onTest, selectedModels, setApiKey, setBaseUrl, setDisplayName, setModelDisplay, setModelId, setName, setSelectedModels, setType, testResult, testStatus, type });
}
