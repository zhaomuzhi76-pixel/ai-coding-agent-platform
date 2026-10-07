import { test, type Page } from "@playwright/test"
import { resetLocalStorageOnce } from "./support/reset"

async function mock(page: Page) {
  await resetLocalStorageOnce(page)
  await page.route("**/api/platform/models", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: { models: [
          { model: "qwen-max", provider: "dashscope",
            display_name: "通义千问-Max", context_window: 32000,
            supports_tool_call: true, supports_stream: true,
            supports_embedding: false,
            cost_input_per_1k: 0.02, cost_output_per_1k: 0.06,
            strengths: ["reasoning"] },
          { model: "claude-sonnet", provider: "anthropic",
            display_name: "Claude Sonnet", context_window: 200000,
            supports_tool_call: true, supports_stream: true,
            supports_embedding: false,
            cost_input_per_1k: 0.003, cost_output_per_1k: 0.015,
            strengths: ["long-context"] },
          { model: "llama3", provider: "ollama",
            display_name: "Llama 3.1", context_window: 128000,
            supports_tool_call: false, supports_stream: true,
            supports_embedding: false,
            cost_input_per_1k: 0, cost_output_per_1k: 0,
            strengths: ["fast", "local"] },
        ] },
      }),
    }),
  )
  await page.route("**/api/platform/domains", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: { domains: [
          { name: "agriculture", entity_types: ["crop", "pesticide"], terms: 2 },
          { name: "finance", entity_types: ["stock", "fund"], terms: 2 },
        ] },
      }),
    }),
  )
  await page.route("**/api/observability/**", (route) => {
    const url = route.request().url()
    if (url.includes("/summary")) {
      return route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          ok: true, data: {
            overall: { count: 42, p50: 12.4, p95: 88.6, p99: 145.2, max: 210.1 },
            spans: 42, errors: 1, alerts: 2,
          },
        }),
      })
    }
    if (url.includes("/spans")) {
      return route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({
          ok: true, data: {
            total: 42,
            spans: [
              { name: "pipeline.propose", span_id: "a", parent_id: null,
                status: "ok", duration_ms: 138.2, error: "",
                attributes: {} },
              { name: "pipeline.apply", span_id: "b", parent_id: "a",
                status: "ok", duration_ms: 22.4, error: "",
                attributes: {} },
              { name: "pipeline.verify", span_id: "c", parent_id: "b",
                status: "error", duration_ms: 410.6, error: "timeout",
                attributes: {} },
            ],
          },
        }),
      })
    }
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: { events: [
          { alert_id: "1", rule: "p95>200ms", severity: "warning",
            message: "pipeline.propose p95 exceeded 200ms",
            context: {}, created_at: Date.now() / 1000 },
        ] },
      }),
    })
  })
  await page.route("**/api/security/**", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: route.request().url().includes("summary")
          ? { roles: 5, permissions: 28, tenants: 3,
              audit_entries: 128, denials: 4 }
          : { roles: [
              { name: "admin", permissions: ["*:manage"], description: "全权限" },
              { name: "developer", permissions: ["tool:execute", "memory:write", "platform:write"], description: "平台/工具/记忆读写" },
              { name: "reviewer", permissions: ["platform:read"], description: "只读+审批" },
              { name: "viewer", permissions: ["platform:read"], description: "只读" },
              { name: "service", permissions: ["platform:execute"], description: "服务账号" },
            ], count: 5 },
      }),
    }),
  )
  await page.route("**/api/mcp/**", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: route.request().url().includes("summary")
          ? { local_tools: 3, remote_servers: 2, domains: 2 }
          : route.request().url().includes("/tools")
            ? { tools: [
                { name: "domain_lookup", description: "查询领域实体",
                  category: "domain", exposed: true, param_count: 3 },
                { name: "domain_search", description: "领域搜索",
                  category: "domain", exposed: true, param_count: 3 },
              ], count: 2 }
            : route.request().url().includes("/servers")
              ? { servers: [
                  { id: "s1", name: "agri-knowledge",
                    endpoint: "stdio://agri-mcp", transport: "stdio",
                    status: "online", tools: 12 },
                  { id: "s2", name: "finance-market",
                    endpoint: "https://api.fin-mcp.local",
                    transport: "sse", status: "online", tools: 8 },
                ], count: 2 }
              : { domains: [], count: 0 },
      }),
    }),
  )
  await page.route("**/api/finetune/**", (route) =>
    route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        ok: true, data: route.request().url().includes("summary")
          ? { recipes: 4, runs: 3, statuses: { done: 1, running: 1, failed: 1 } }
          : route.request().url().includes("/recipes")
            ? { recipes: [
                { name: "lora-quick", description: "LoRA 快速试验：r=4, 2 epochs" },
                { name: "lora-balanced", description: "LoRA 平衡：r=8, 3 epochs" },
                { name: "lora-quality", description: "LoRA 高质：r=32, 5 epochs" },
                { name: "prefix-tuning", description: "Prefix Tuning：20 virtual tokens" },
              ], count: 4 }
            : { runs: [
                { id: "ft-001", method: "lora", base_model: "Qwen/Qwen2.5-7B",
                  epochs: 3, samples: 1240, status: "done",
                  progress: 100, loss: 0.412, saved_to: "/runs/ft-001" },
                { id: "ft-002", method: "prefix", base_model: "Qwen/Qwen2.5-7B",
                  epochs: 2, samples: 820, status: "running",
                  progress: 62, loss: 0.583, saved_to: "/runs/ft-002" },
              ], count: 2 },
      }),
    }),
  )
}

const TABS = [
  ["platform", "01-platform"],
  ["models", "02-models"],
  ["finetune", "03-finetune"],
  ["mcp", "04-mcp"],
  ["security", "05-security"],
  ["monitor", "06-monitor"],
]

test.describe("Screenshots", () => {
  for (const [tab, name] of TABS) {
    test(`screenshot ${tab}`, async ({ page }) => {
      await mock(page)
      await page.goto(`/#/${tab}`)
      await page.waitForTimeout(800)
      await page.screenshot({
        path: `e2e/screenshots/${name}.png`,
        fullPage: true,
      })
      console.log(`  [shot] ${name}.png`)
    })
  }

  test("screenshot light theme", async ({ page }) => {
    await mock(page)
    await page.goto("/#/platform")
    await page.evaluate(() => {
      localStorage.setItem("biancheng.theme", "light")
    })
    await page.reload()
    await page.waitForTimeout(500)
    await page.screenshot({
      path: "e2e/screenshots/07-light-theme.png",
      fullPage: true,
    })
    console.log(`  [shot] 07-light-theme.png`)
  })

  test("screenshot en locale", async ({ page }) => {
    await mock(page)
    await page.goto("/#/platform")
    await page.evaluate(() => {
      localStorage.setItem("biancheng.ai.locale", "en-US")
    })
    await page.reload()
    await page.waitForTimeout(500)
    await page.screenshot({
      path: "e2e/screenshots/08-en-locale.png",
      fullPage: true,
    })
    console.log(`  [shot] 08-en-locale.png`)
  })
})
