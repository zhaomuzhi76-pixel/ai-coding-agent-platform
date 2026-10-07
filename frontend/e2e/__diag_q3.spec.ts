import { test } from "@playwright/test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

test.setTimeout(45000)

test("[3] 只读查询诊断", async ({ page }) => {
  const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "diag-q3-"))
  for (let i = 0; i < 5; i++) {
    fs.writeFileSync(path.join(TMP, `m${i}.py`), "")
  }

  const wsFrames: string[] = []
  const consoleErrors: string[] = []

  page.on("websocket", (ws) => {
    ws.on("framesent", (f) =>
      wsFrames.push(`SENT ${ws.url().split("/").pop()}: ${String(f.payload).slice(0, 200)}`),
    )
    ws.on("framereceived", (f) =>
      wsFrames.push(`RECV ${ws.url().split("/").pop()}: ${String(f.payload).slice(0, 300)}`),
    )
  })
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text().slice(0, 200))
  })

  const url = `/#/coding?workspace=${encodeURIComponent(TMP)}`
  await page.goto(url, { waitUntil: "domcontentloaded" })
  await page.reload({ waitUntil: "domcontentloaded" })

  // 等 Ready
  try {
    await page.waitForFunction(
      () => document.querySelector(".agent-composer__status")?.textContent?.trim() === "Ready",
      { timeout: 25000 },
    )
    console.log("[状态] Ready ✅")
  } catch {
    const st = await page.locator(".agent-composer__status").textContent().catch(() => "?")
    console.log(`[状态] 未达 Ready: ${st}`)
  }

  // 检查 workspace chip
  const wsChip = await page.locator(".agent-composer__chip").first().textContent().catch(() => "?")
  console.log(`[workspace chip] ${wsChip}`)

  // 发消息
  const ta = page.locator("textarea[aria-label='Agent message']")
  if (await ta.count() === 0) {
    console.log("❌ 没有输入框")
    return
  }
  await ta.fill("当前项目有多少个 py 文件")
  await page.waitForTimeout(400)
  await page.keyboard.press("Control+Enter")

  // 等 20 秒
  let hasCount = false
  for (let i = 1; i <= 10; i++) {
    await page.waitForTimeout(2000)
    const body = await page.locator("body").innerText()
    hasCount = /\d+\s*个\s*\.py/.test(body)
    if (hasCount) {
      console.log(`[+${i * 2}s] 结果出现 ✅`)
      break
    }
  }
  if (!hasCount) console.log("[超时] 20 秒内未出现结果")

  console.log("\n════ WS 帧 ════")
  if (wsFrames.length === 0) console.log("  (无)")
  wsFrames.forEach((f) => console.log("  " + f))

  console.log("\n════ Console 错误 ════")
  if (consoleErrors.length === 0) console.log("  (无)")
  consoleErrors.forEach((e) => console.log("  " + e))

  console.log("\n════ body 尾部 500 字符 ════")
  const body = await page.locator("body").innerText()
  console.log(body.slice(-500))
})
