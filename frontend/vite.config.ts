import react from "@vitejs/plugin-react"
import { defineConfig, loadEnv } from "vite"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const backendTarget = env.VITE_BACKEND_URL || "http://127.0.0.1:9022"

  return {
    base: "./",
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: 4173,
      strictPort: true,
      proxy: {
      "/data": {
        target: "http://127.0.0.1:9022",
        changeOrigin: true,
      },

        "/api/health": {
          target: backendTarget, changeOrigin: true,
          rewrite: () => "/health",
        },
        "/api": { target: backendTarget, changeOrigin: true, ws: true },
        "/ws/agent": { target: backendTarget, changeOrigin: true, ws: true },
        "/ws/platform": { target: backendTarget, changeOrigin: true, ws: true },
      },
    },
    preview: {
      host: "0.0.0.0",
      port: 4173,
      strictPort: true,
    },
    build: {
      outDir: "dist",
      emptyOutDir: true,
      assetsDir: "assets",
    },
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || "0.0.0"),
    },
  }
})
