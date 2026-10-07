import { test } from "@playwright/test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

const FIXTURE = fs.mkdtempSync(path.join(os.tmpdir(), "diag-q-"))
for (let i = 0; i < 5; i++) {
  fs.writeFileSync(path.join(FIXTURE, `m${i}.py`), "")
}

test.setTimeout(60000)

test("[3] 段专项诊断", async ({ page }) => {
  const wsFrames: string[] = []
  const consoleLogs: string[] = []
  const pageErrors: string[] = []

  page.on("websocket", (ws) => {
    ws.on("framesent", (f) =>
      wsFrames.push(`SENT ${ws.url().split("/").slice(-2).join("/")}: ${String(f.payload).slice(0, 300)}`),
    )
    ws.on("framereceived", (f) =>
      wsFrames.push(`RECV ${ws.url().split("/").slice(-2).join("/")}: ${String(f.payload).slice(0, 400)}`),
    )
  })
  page.on("console", (m) => consoleLogs.push(`[${m.type()}] ${m.text().slice(0, 250)}`))
  page.on("pageerror", (e) => pageErrors.push(e.message.slice(0, 300)))

  const url = `/#/coding?workspace=${encodeURIComponent(FIXTURE)}`
  console.log(`\n[URL] ${url}`)

  await page.goto(url, { waitUntil: "domcontentloaded" })
  await page.reload({ waitUntil: "domcontentloaded" })

  // 等 Ready
  try {
    await page.waitForFunction(
      () => document.querySelector(".agent-composer__status")?.textContent?.trim() === "Ready",
      { timeout: 30000 },
    )
    console.log("[状态] Ready ✅")
  } catch {
    const st = await page.locator(".agent-composer__status").textContent().catch(() => "?")
    console.log(`[状态] 未达 Ready: ${st}`)
  }

  // 发消息
  const ta = page.locator("textarea[aria-label='Agent message']")
  await ta.fill("当前项目有多少个 py 文件")
  await page.waitForTimeout(500)
  await page.keyboard.press("Control+Enter")

  // 等 20 秒结果
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
  wsFrames.forEach((f) => console.log("  " + f))

  console.log("\n════ Console（关键）════")
  consoleLogs
    .filter((l) => /session|error|query|dispatch|restore|bootstrap|step/i.test(l))
    .slice(0, 20)
    .forEach((l) => console.log("  " + l))

  console.log("\n════ pageerror ════")
  pageErrors.length === 0
    ? console.log("  (无)")
    : pageErrors.forEach((e) => console.log("  " + e))

  console.log("\n════ body 尾部 600 字符 ════")
  const body = await page.locator("body").innerText()
  console.log(body.slice(-600))
})
