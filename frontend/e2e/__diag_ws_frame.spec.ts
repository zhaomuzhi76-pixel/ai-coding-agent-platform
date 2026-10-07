import { test } from "@playwright/test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

const FIXTURE = fs.mkdtempSync(path.join(os.tmpdir(), "diag-ws-"))
for (let i = 0; i < 5; i++) {
  fs.writeFileSync(path.join(FIXTURE, `m${i}.py`), "")
}

test.setTimeout(90000)

test("WS 帧原文", async ({ page }) => {
  const 帧列表: string[] = []

  page.on("websocket", (ws) => {
    ws.on("framereceived", (f) => {
      const s = String(f.payload)
      if (s.includes('"type":"result"') || s.includes('"type":"step"')) {
        帧列表.push(s)
      }
    })
  })

  const url = `/#/coding?workspace=${encodeURIComponent(FIXTURE)}`
  await page.goto(url, { waitUntil: "domcontentloaded" })
  await page.reload({ waitUntil: "domcontentloaded" })

  await page.waitForFunction(
    () => document.querySelector(".agent-composer__status")?.textContent?.trim() === "Ready",
    { timeout: 30000 },
  ).catch(() => undefined)

  const ta = page.locator("textarea[aria-label='Agent message']")
  await ta.fill("当前项目有多少个 py 文件")
  await page.keyboard.press("Control+Enter")

  // 等 25 秒
  await page.waitForTimeout(25000)

  console.log(`\n════ 收到 ${帧列表.length} 个 WS 帧 ════`)
  帧列表.forEach((s, i) => {
    console.log(`\n[${i}] ${s.length} 字符`)
    console.log(s.slice(0, 900))
  })
})
