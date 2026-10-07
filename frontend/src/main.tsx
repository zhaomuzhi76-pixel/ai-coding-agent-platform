import React from "react"
import ReactDOM from "react-dom/client"

import { App } from "./app/App"
import { ErrorBoundary } from "./app/integration/error_boundary"
import { installGlobalErrorHandler } from "./app/integration/global_error_handler"
import { safeStartup } from "./app/integration/startup_safe"
import { initTheme } from "./core/theme/theme"

import "./app/app.css"

// 启动顺序（关键）：
// 1. 全局错误捕获（最早，捕获后续所有错误）
// 2. 启动安全（清损坏 storage）
// 3. 主题初始化
installGlobalErrorHandler()
safeStartup()
initTheme()

const rootEl = document.getElementById("root")
if (!rootEl) {
  document.body.innerHTML =
    '<div style="padding:24px;color:#ef8585;font-family:monospace">' +
    '❌ #root 缺失（index.html 异常）' +
    '</div>'
  throw new Error("root element missing")
}

ReactDOM.createRoot(rootEl).render(
  <ErrorBoundary label="app-root">
      <App />
    </ErrorBoundary>,
)
