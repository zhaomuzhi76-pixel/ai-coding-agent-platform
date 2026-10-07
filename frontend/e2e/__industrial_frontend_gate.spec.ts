import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

// 工业级 fixture：真实临时目录 + 5 个 py 文件
const FIXTURE_DIR = fs.mkdtempSync(
  path.join(os.tmpdir(), "industrial-e2e-fixture-"),
)
for (let i = 0; i < 5; i++) {
  fs.writeFileSync(path.join(FIXTURE_DIR, `mod_${i}.py`), "")
}
fs.writeFileSync(path.join(FIXTURE_DIR, "README.md"), "")

import { test, expect } from "@playwright/test"

test.setTimeout(90000)

interface Diag {
  name: string
  pass: boolean
  detail: string
}
const diag: Diag[] = []
function record(name: string, pass: boolean, detail = "") {
  diag.push({ name, pass, detail })
  const icon = pass ? "PASS" : "FAIL"
  console.log(`  [${icon}] ${name}${detail ? `  -> ${detail}` : ""}`)
}

test("工业级前端整体测试", async ({ page }) => {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []

  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text())
  })
  page.on("pageerror", (e) => pageErrors.push(e.message))

  // ═══════════════════════════════════════════════
  // 1) Coding 页加载
  // ═══════════════════════════════════════════════
  console.log("\n─── [1] Coding 页加载 ───")
  await page.goto("/#/coding", { waitUntil: "domcontentloaded" })
  await page.waitForTimeout(3000)

  const composer = page.locator(".agent-composer")
  record("composer 存在", (await composer.count()) > 0)

  const textarea = page.locator("textarea[aria-label='Agent message']")
  record("输入框存在", (await textarea.count()) > 0)

  // ═══════════════════════════════════════════════
  // 2) 模型下拉
  // ═══════════════════════════════════════════════
  console.log("\n─── [2] 模型下拉 ───")
  const selects = page.locator("select")
  const nSel = await selects.count()
  record("select 数量 >= 1", nSel >= 1, `count=${nSel}`)

  if (nSel >= 1) {
    const opts = await selects.first().locator("option").allTextContents()
    record("模型选项非空", opts.length > 0, `options=${opts.length}`)
    const current = await selects.first().inputValue()
    record("模型有默认值", !!current, `value=${current}`)
  }

  // ═══════════════════════════════════════════════
  // 3) 只读查询（核心能力）
  // ═══════════════════════════════════════════════
  console.log("\n─── [3] 只读查询（URL 参数 + 真实 workspace）───")
  const url = `/#/coding?workspace=${encodeURIComponent(FIXTURE_DIR)}`
  await page.goto(url, { waitUntil: "domcontentloaded" })
  // hash 变化不触发浏览器重载 → 强制 reload 让 React 重新挂载
  // 以便读取 ?workspace= 参数（工业级 E2E 处理 hash-only nav）
  await page.reload({ waitUntil: "domcontentloaded" })

  // 工业级条件等待：等 composer 状态变 Ready（session bootstrap 完成）
  await page
    .waitForFunction(
      () => {
        const el = document.querySelector(".agent-composer__status")
        return el?.textContent?.trim() === "Ready"
      },
      { timeout: 30000 },
    )
    .catch(() => undefined)

  const textarea2 = page.locator("textarea[aria-label='Agent message']")
  if (await textarea2.count() > 0) {
    await textarea2.fill("当前项目有多少个 py 文件")
    await page.keyboard.press("Control+Enter")

    // 工业级条件等待：等结果文本出现（最多 20 秒）
    let hasCount = false
    try {
      await page.waitForFunction(
        () => /\d+\s*个\s*\.py/.test(document.body.innerText),
        { timeout: 20000 },
      )
      hasCount = true
    } catch {
      hasCount = false
    }

    const body = await page.locator("body").innerText()
    const hasError = /workspace not found|unknown\.py|cannot read/.test(body)

    record("查询返回文件数", hasCount)
    record("查询无旧错误", !hasError)
  }

  // ═══════════════════════════════════════════════
  // 4) 分隔条存在
  // ═══════════════════════════════════════════════
  console.log("\n─── [4] 布局分隔条 ───")
  const handles = page.locator(".vertical-split__handle")
  const nHandle = await handles.count()
  record("分隔条数量 >= 1", nHandle >= 1, `count=${nHandle}`)

  if (nHandle > 0) {
    const box = await handles.first().boundingBox()
    record("分隔条可见", !!box && box.height > 0,
      `h=${box?.height ?? 0}`)
  }

  // ═══════════════════════════════════════════════
  // 5) 编辑器偏好控件
  // ═══════════════════════════════════════════════
  console.log("\n─── [5] 编辑器偏好控件 ───")
  const prefs = page.locator(".editor-prefs")
  record("偏好控件存在", (await prefs.count()) > 0)
  if (await prefs.count() > 0) {
    const swatches = await prefs.first()
      .locator(".editor-prefs__swatch").count()
    record("色板方块 >= 4", swatches >= 4, `swatches=${swatches}`)
  }

  // ═══════════════════════════════════════════════
  // 6) 无 console / page 错误
  // ═══════════════════════════════════════════════
  console.log("\n─── [6] 无致命错误 ───")
  const realErrors = consoleErrors.filter(
    (e) => !/DevTools|favicon|websocket.*closed|React DevTools/i.test(e),
  )
  record("无页面崩溃", pageErrors.length === 0,
    pageErrors.length ? pageErrors[0] : "")
  record("无 console 错误", realErrors.length === 0,
    realErrors.length ? realErrors[0].slice(0, 120) : "")

  // ═══════════════════════════════════════════════
  // 7) 其它页面能打开
  // ═══════════════════════════════════════════════
  console.log("\n─── [7] 其它页面可访问 ───")
  for (const path of ["/#/platform", "/#/"]) {
    await page.goto(path, { waitUntil: "domcontentloaded" })
    await page.waitForTimeout(1500)
    const bodyLen = (await page.locator("body").innerText()).length
    record(`页面 ${path} 渲染`, bodyLen > 50, `bodyLen=${bodyLen}`)
  }

  // ═══════════════════════════════════════════════
  // 8) 截图
  // ═══════════════════════════════════════════════
  await page.goto("/#/coding", { waitUntil: "domcontentloaded" })
  await page.waitForTimeout(2000)
  await page.screenshot({
    path: "e2e/screenshots/__industrial_frontend_gate.png",
    fullPage: true,
  })

  // ═══════════════════════════════════════════════
  // 汇总
  // ═══════════════════════════════════════════════
  const total = diag.length
  const passed = diag.filter((d) => d.pass).length
  const failed = total - passed

  console.log("\n" + "=".repeat(51))
  console.log(`  前端整体测试: ${passed}/${total}`)
  console.log(`  结果: ${failed === 0 ? "全部通过" : `${failed} 个失败`}`)
  console.log("=".repeat(51))

  expect(failed).toBe(0)
})
