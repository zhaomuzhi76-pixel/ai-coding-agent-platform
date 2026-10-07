/** 后端模型加载 + 自动选默认（工业级：首次打开无需手动点选）。 */
import { useCallback, useEffect, useState } from "react"

import {
  loadBackendModels,
  type BackendModel,
} from "../../../core/models/backend_models_source"
import { loadModelPreference } from "../persistence/model_preference_local_store"

import { toLegalProvider } from "./agent_workspace_label"

// [FOLLOW_ROLE_SENTINEL] 与 agent_composer_context 的 FOLLOW_ROLE 保持一致
export const FOLLOW_ROLE_SENTINEL = "__follow_role__"

export interface ModelSelectionController {
  setModelSelection(input: {
    provider: "ollama" | "openai_compatible"
    model: string
    base_url: string
    api_key: string
  }): void
}

export function useBackendModels(
  currentModel: string,
  controller: ModelSelectionController,
) {
  const [backendModels, setBackendModels] = useState<BackendModel[]>([])

  // 1. 从配置中心拉可用模型（health 过滤）
  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const models = await loadBackendModels()
        if (!cancelled) setBackendModels(models)
      } catch {
        // 静默失败：保留空列表，用户可手动选择
      }
    })()
    return () => { cancelled = true }
  }, [])

  // 2. 自动选默认模型（存储优先 → 首个）
  useEffect(() => {
    if (backendModels.length === 0) return
    // [FOLLOW_ROLE_SENTINEL] 用户选"跟随"→ 不自动填
    if (currentModel === FOLLOW_ROLE_SENTINEL) return
    if (currentModel) return

    const stored = loadModelPreference()
    const match = stored
      ? backendModels.find((m) => m.model === stored.model)
      : null

    const pick = (stored && match) ? match : backendModels[0]
    controller.setModelSelection({
      provider: toLegalProvider(pick.provider_type),
      model: pick.model,
      base_url: pick.base_url ?? "",
      api_key: "",
    })
  }, [backendModels, currentModel, controller])

  const onSelectModel = useCallback((modelId: string) => {
      // [FOLLOW_ROLE_SENTINEL] 跟随角色配置
      if (modelId === FOLLOW_ROLE_SENTINEL) {
        controller.setModelSelection({
          provider: "ollama", model: FOLLOW_ROLE_SENTINEL,
          base_url: "", api_key: "",
        })
        return
      }
    const m = backendModels.find((x) => x.model === modelId)
    if (!m) return
    controller.setModelSelection({
      provider: toLegalProvider(m.provider_type),
      model: m.model,
      base_url: m.base_url ?? "",
      api_key: "",
    })
  }, [backendModels, controller])

  return { backendModels, onSelectModel }
}
