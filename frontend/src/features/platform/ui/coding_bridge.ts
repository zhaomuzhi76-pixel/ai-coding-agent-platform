/**
 * Platform → Coding Tab 的文件打开桥。
 *
 * 职责：
 *   platform 提案详情里点「在 IDE 中查看」时，
 *   把目标文件路径写进 localStorage，
 *   然后切到 #/coding。
 *
 * coding Tab 一侧如果已有"待打开文件"消费机制就自动生效；
 * 没有也不影响（用户手动从文件树打开）。
 */
const OPEN_FILE_KEY = "biancheng.pending.openFile"

export function openInCodingTab(filePath: string): void {
  if (!filePath || !filePath.trim()) return
  try {
    window.localStorage.setItem(OPEN_FILE_KEY, filePath.trim())
  } catch {
    // ignore
  }
  window.location.hash = "#/coding"
}

export function consumePendingFile(): string | null {
  try {
    const v = window.localStorage.getItem(OPEN_FILE_KEY)
    if (v) {
      window.localStorage.removeItem(OPEN_FILE_KEY)
      return v
    }
  } catch {
    // ignore
  }
  return null
}
