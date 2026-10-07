import type { Locale } from "./locale"
import { CORE, type CoreKey } from "./messages_core"
import { PAGES, type PageKey } from "./messages_pages"

export type MessageKey = CoreKey | PageKey

const merged: Record<Locale, Record<MessageKey, string>> = {
  "zh-CN": { ...CORE["zh-CN"], ...PAGES["zh-CN"] },
  "en-US": { ...CORE["en-US"], ...PAGES["en-US"] },
}

export function message(
  locale: Locale,
  key: MessageKey,
): string {
  const table = merged[locale] ?? merged["zh-CN"]
  return table[key] ?? key
}
