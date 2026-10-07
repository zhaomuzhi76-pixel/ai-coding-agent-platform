import { test, expect } from "@playwright/test"
import * as fs from "fs"
import * as os from "os"
import * as path from "path"

test.setTimeout(180000)

test("platform WS 流式 push", async ({ page }) => {
  const ws = fs.mkdtempSync(path.join(os.tmpdir(), "e2e_ws_"))
  fs.writeFileSync(
    path.join(ws, "calc.py"),
    'def add(a, b):\n    return a - b\n',
  )
  console.log(`  [ws] ${ws}`)

  await page.goto("/#/platform")
  await page.waitForTimeout(2000)

  const wsInput = page.locator("input[placeholder='/path/to/project']")
  await wsInput.fill(ws)
  await wsInput.blur()

  const modelSelect = page.locator("select").first()
  const options = await modelSelect.locator("option").allTextContents()
  console.log(`  [2] options: ${options.join(" | ")}`)
  const target = options.find((o) => o.includes("3.8") || o.includes("maas"))
  if (target) {
    await modelSelect.selectOption({ label: target })
    console.log(`  [2] model: ${target}`)
  }

  // 等按钮 enable（workspace + model 都设好）
  const btn = page.getByRole("button", { name: "新建会话" })
  await expect(btn).toBeEnabled({ timeout: 10000 })
  await btn.click()
  await page.waitForTimeout(3000)

  const textarea = page.locator("textarea").first()
  await textarea.fill("修复 calc.py 的 add 函数：让 add(1,2)=3")
  const filesInput = page.locator("input[placeholder*='目标文件']")
  await filesInput.fill("calc.py")

  await page.getByRole("button", { name: "生成提案" }).click()
  console.log("  [4] 点击生成，等 WS token 流...")

  // 等实时日志面板出现
  await expect(page.locator("text=实时日志")).toBeVisible({ timeout: 20000 })
  console.log("  [5] 实时日志面板已出现")

  // 等 done（proposal 出现）
  await expect(page.locator(".proposal-card").first()).toBeVisible({
    timeout: 120000,
  })
  console.log("  [6] proposal 出现")

  // 检查 token 是否推送（日志面板文本长度 > 100）
  const logText = await page.locator("text=实时日志").locator("..").innerText()
  console.log(`  [7] 日志长度: ${logText.length}`)
  expect(logText.length).toBeGreaterThan(100)
  console.log("  ✓ PASS: 流式 token 到达前端")
})
