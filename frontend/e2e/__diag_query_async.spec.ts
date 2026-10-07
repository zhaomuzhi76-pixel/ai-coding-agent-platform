import { test } from "@playwright/test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

const FIXTURE = fs.mkdtempSync(path.join(os.tmpdir(), "diag-async-"))
for (let i = 0; i < 5; i++) {
  fs.writeFileSync(path.join(FIXTURE, `m${i}.py`), "")
}

test.setTimeout(60000)

test("[3] async 改造后诊断", async ({ page }) => {
  const wsFrames: string[] = []
  const logs: string[] = []

  page.on("websocket", (ws) => {
    ws.on("framesent", (f) =>
      wsFrames.push(`SENT ${ws.url().split("/").pop()}: ${String(f.payload).slice(0, 200)}`),
    )
    ws.on("framereceived", (f) =>
      wsFrames.push(`RECV ${ws.url().split("/").pop()}: ${String(f.payload).slice(0, 400)}`),
    )
  })
  page.on("console", (m) => logs.push(`[${m.type()}] ${m.text().slice(0, 200)}`))
  page.on("pageerror", (e) => logs.push(`[pageerror] ${e.message.slice(0, 200)}`))

  const url = `/#/coding?workspace=${encodeURIComponent(FIXTURE)}`
  await page.goto(url, { waitUntil: "domcontentloaded" })
  await page.reload({ waitUntil: "domcontentloaded" })

  await page.waitForFunction(
    () => document.querySelector(".agent-composer__status")?.textContent?.trim() === "Ready",
    { timeout: 30000 },
  ).catch(() => undefined)

  const ta = page.locator("textarea[aria-label='Agent message']")
  await ta.fill("当前项目有多少个 py 文件")
  await page.waitForTimeout(300)
  // 优先点 Send 按钮，避免 Ctrl+Enter 被 isComposing 拦截
  const sendBtn = page.locator("button[type='submit']")
  if (await sendBtn.count() > 0) {
    await sendBtn.click()
  } else {
    await page.keyboard.press("Control+Enter")
  }

  // 等待 25 秒
  let hasCount = false
  for (let i = 1; i <= 12; i++) {
    await page.waitForTimeout(2000)
    const body = await page.locator("body").innerText()
    hasCount = /\d+\s*个\s*\.py/.test(body)
    if (hasCount) {
      console.log(`[+${i * 2}s] 结果出现 ✅`)
      break
    }
  }
  if (!hasCount) console.log("[超时] 24 秒内未出现结果")

  console.log("\n════ WS 帧 ════")
  wsFrames.forEach((f) => console.log("  " + f))

  console.log("\n════ Console ════")
  logs
    .filter((l) => /error|session|query|dispatch|step/i.test(l))
    .slice(0, 20)
    .forEach((l) => console.log("  " + l))

  console.log("\n════ body 尾部 800 字符 ════")
  const body = await page.locator("body").innerText()
  console.log(body.slice(-800))
})
