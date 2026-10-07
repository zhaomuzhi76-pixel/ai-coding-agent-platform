import { useState } from "react"

import {
  PlatformController,
} from "../../../features/platform/platform_controller"
import {
  createPlatformGateway,
} from "../../../features/platform/platform_gateway"
import {
  PlatformWorkbench,
} from "../../../features/platform/ui"

const WORKSPACE_KEYS = [
  "biancheng.platform.workspace",   // 平台专用
  "biancheng.workspace.root",       // 编码 Tab 项目根
  "biancheng.workspace",            // 兼容
  "biancheng.project.workspace",    // 项目会话
]

function findWorkspace(): string {
  try {
    for (const k of WORKSPACE_KEYS) {
      const v = window.localStorage.getItem(k)
      if (v && v.trim()) return v.trim()
    }
  } catch {
    // ignore
  }
  return ""
}

export function PlatformWorkbenchEntry() {
  const [controller] = useState(
    () => new PlatformController(createPlatformGateway()),
  )
  return (
    <PlatformWorkbench
      controller={controller}
      defaultWorkspace={findWorkspace()}
      userId="default"
      locale="zh-CN"
    />
  )
}
