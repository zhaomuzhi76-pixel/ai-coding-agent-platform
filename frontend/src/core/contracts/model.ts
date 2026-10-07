export type ModelProvider =
  | "ollama"
  | "openai_compatible"
  | "dashscope"
  | "anthropic"

const VALID_PROVIDERS: readonly ModelProvider[] = [
  "ollama",
  "openai_compatible",
  "dashscope",
  "anthropic",
]

export interface ModelSelection {
  provider: ModelProvider
  model: string
  base_url: string
  api_key: string
}

export function validateModelSelection(
  value: ModelSelection,
): void {
  if (!VALID_PROVIDERS.includes(value.provider)) {
    throw new Error("unsupported model provider")
  }

  if (
    typeof value.model !== "string"
    || !value.model.trim()
  ) {
    throw new Error("model required")
  }

  // 只有 ollama 允许空 base_url（走本机 11434）
  if (
    value.provider !== "ollama"
    && !value.base_url.trim()
  ) {
    throw new Error("base_url required")
  }
}
