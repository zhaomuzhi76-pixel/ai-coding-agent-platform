import type { ReactNode } from "react"
import { TerminalPanel } from "../../../core/terminal/terminal_panel"
import "../../../core/terminal/terminal_panel.css"
import { useEffect, useRef } from "react"

import { IdeWorkspaceLayout } from "./ide_workspace_layout"
import { IdeSurfaceRegistry } from "./ide_surface_registry"

type Props = {
  sidebar?: ReactNode
  model?: ReactNode
  prompt?: ReactNode
  runtime?: ReactNode
  code?: ReactNode
  execution?: ReactNode
  terminal?: ReactNode
  review?: ReactNode
  surfaces?: IdeSurfaceRegistry
  state?: unknown
  store?: unknown
  controller?: unknown
  workspace?: unknown
}

export function IndustrialCodexWorkspace(props: Props) {
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = root.current
    if (!el) {
      return
    }
    const container = el
    const cleanups: Array<() => void> = []

    function drag(
      selector: string,
      css: string,
      reverse = false,
    ) {
      const handle = container.querySelector(selector)
      if (!handle) {
        return
      }
      let active = false
      const onMouseDown = () => {
        active = true
      }
      const onMouseUp = () => {
        active = false
      }
      const onMouseMove = (event: MouseEvent) => {
        if (!active) {
          return
        }
        const value = reverse
          ? window.innerWidth - event.clientX
          : event.clientX
        container.style.setProperty(css, `${value}px`)
      }
      handle.addEventListener("mousedown", onMouseDown)
      window.addEventListener("mouseup", onMouseUp)
      window.addEventListener("mousemove", onMouseMove)
      cleanups.push(() => {
        handle.removeEventListener("mousedown", onMouseDown)
        window.removeEventListener("mouseup", onMouseUp)
        window.removeEventListener("mousemove", onMouseMove)
      })
    }

    drag(".workspace-sidebar-resize", "--workspace-sidebar-width")
    drag(".workspace-agent-resize", "--workspace-agent-width", true)

    return () => {
      cleanups.forEach(cleanup => cleanup())
    }
  }, [])

  const surfaceContext = {
    state: props.state,
    store: props.store,
    controller: props.controller,
    workspace: props.workspace,
  }

  return (
    <div ref={root} className="ide-workspace-root">
      <div className="workspace-sidebar-resize" />

      <IdeWorkspaceLayout
        sidebar={
          props.sidebar ??
          props.surfaces?.resolve("sidebar", surfaceContext) ??
          null
        }
        prompt={
          props.prompt ??
          props.surfaces?.resolve("prompt", surfaceContext)
        }
        code={
          props.code ??
          props.surfaces?.resolve("code", surfaceContext)
        }
        execution={
          props.execution ??
          props.surfaces?.resolve("execution", surfaceContext)
        }
        terminal={<TerminalPanel />}
        review={
          props.review ??
          props.surfaces?.resolve("review", surfaceContext)
        }
      />

      <div className="workspace-agent-resize" />
    </div>
  )
}
