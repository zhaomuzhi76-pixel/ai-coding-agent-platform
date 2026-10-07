import type { ModelSelection } from "../../../core/contracts/model"
import {
  ModelCatalog,
  type ModelProfile,
} from "../../../core/models/model_catalog"
import {
  BrowserModelCatalogStorage,
} from "../../../core/models/model_catalog_storage"
import { OLLAMA_URL } from "../../../core/config/runtime"

export interface ModelForm {
  label: string
  provider: ModelSelection["provider"]
  model: string
  base_url: string
  api_key: string
}

export const DEFAULT_PROFILES: ModelProfile[] = [
  {
    id: "ollama-qwen35",
    label: "Qwen 3.5 Local",
    provider: "ollama",
    model: "qwen3.5:0.8b",
    base_url: OLLAMA_URL,
    api_key: "",
  },
  {
    id: "openai-gpt41",
    label: "OpenAI GPT-4.1",
    provider: "openai_compatible",
    model: "gpt-4.1",
    base_url: "https://api.openai.com/v1",
    api_key: "",
  },
]

export function emptyModelForm(): ModelForm {
  return {
    label: "",
    provider: "ollama",
    model: "",
    base_url: OLLAMA_URL,
    api_key: "",
  }
}

export function loadModelCatalog(
  storage: BrowserModelCatalogStorage,
): ModelCatalog {
  try {
    const saved = storage.load()
    if (saved.length) {
      return new ModelCatalog(saved)
    }
  } catch {
    storage.clear()
  }

  return new ModelCatalog(DEFAULT_PROFILES)
}

export function persistModelCatalog(
  storage: BrowserModelCatalogStorage,
  catalog: ModelCatalog,
): void {
  storage.save(catalog.list())
}
