import { defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "happy-dom",
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    exclude: [
      "frontend/e2e/**",
      "**/e2e/**",
      "node_modules/**",
      "e2e/**",
    ],
  },
})
