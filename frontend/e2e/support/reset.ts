import type { Page } from "@playwright/test"

/**
 * Seed default locale / theme ONLY if absent.
 *
 * 关键：reload 时 storage 已有值则不覆盖，
 * 否则会破坏「刷新后持久」的断言。
 *
 * Playwright 每 test 独立 context，首次进入 storage 为空，
 * 因此会写入 zh-CN + dark，后续 reload 保持。
 */
export async function resetLocalStorageOnce(page: Page): Promise<void> {
  await page.addInitScript(() => {
    try {
      if (!window.localStorage.getItem("biancheng.ai.locale")) {
        window.localStorage.setItem("biancheng.ai.locale", "zh-CN")
      }
      if (!window.localStorage.getItem("biancheng.theme")) {
        window.localStorage.setItem("biancheng.theme", "dark")
      }
    } catch {
      // ignore
    }
  })
}

export async function clearStorageNow(page: Page): Promise<void> {
  await page.evaluate(() => {
    try {
      window.localStorage.clear()
    } catch {
      // ignore
    }
  })
}
