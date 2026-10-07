export type Locale = "zh-CN" | "en-US"

const STORAGE_KEY = "biancheng.ai.locale"

export function readLocale(): Locale {
  const value = window.localStorage.getItem(STORAGE_KEY)
  return value === "en-US" ? "en-US" : "zh-CN"
}

export function writeLocale(locale: Locale): void {
  window.localStorage.setItem(STORAGE_KEY, locale)
}
