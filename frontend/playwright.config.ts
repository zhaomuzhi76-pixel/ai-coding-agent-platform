import { defineConfig } from "@playwright/test"

export default defineConfig({
  testDir: "./e2e",
  testIgnore: ["**/frontend_real_surface.spec.ts"],
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    headless: true,
    viewport: { width: 1440, height: 900 },
    actionTimeout: 8000,
  },
  webServer: {
    command: "npm run dev:vite",
    port: 4173,
    reuseExistingServer: true,
    timeout: 60000,
  },
})
