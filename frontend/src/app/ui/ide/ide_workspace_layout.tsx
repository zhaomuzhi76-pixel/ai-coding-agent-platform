import type { ReactNode } from "react"
import { useCallback, useEffect, useRef } from "react"
import {
  useVerticalSplit,
  VerticalSplitHandle,
} from "../../../core/layout/vertical_split"
import "../../../core/layout/vertical_split/ide_main_split.css"
import "../../../core/layout/vertical_split/vertical_split.css"
import { EditorPreferencesControls } from "../../../core/editor_preferences"
import { SidebarResizer } from "../../../core/layout/sidebar_resize"

interface Props {
  sidebar?: ReactNode
  code?: ReactNode
  prompt?: ReactNode
  execution?: ReactNode
  terminal?: ReactNode
  review?: ReactNode
}

const MIN_TOP = 80
const MIN_BOTTOM = 120
const HANDLE = 14

export function IdeWorkspaceLayout(props: Props) {
  const mainSplit = useVerticalSplit({
    storageKey: "biancheng.ide.main.split",
    defaultRatio: 0.66,
  })
  const footerSplit = useVerticalSplit({
    storageKey: "biancheng.ide.footer.split",
    defaultRatio: 0.72,
    minRatio: 0.45,
    maxRatio: 0.92,
  })

  const rightRef = useRef<HTMLElement>(null)
  const dragging = useRef(false)

  useEffect(() => {
    function onMove(e: MouseEvent) {
      if (!dragging.current || !rightRef.current) return
      const rect = rightRef.current.getBoundingClientRect()
      const y = e.clientY - rect.top
      const top = Math.min(Math.max(y, MIN_TOP), rect.height - MIN_BOTTOM)
      rightRef.current.style.setProperty("--right-top-h", `${top}px`)
    }
    function onUp() {
      if (!dragging.current) return
      dragging.current = false
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
    window.addEventListener("mousemove", onMove)
    window.addEventListener("mouseup", onUp)
    return () => {
      window.removeEventListener("mousemove", onMove)
      window.removeEventListener("mouseup", onUp)
    }
  }, [])

  const onDown = useCallback(() => {
    dragging.current = true
    document.body.style.cursor = "row-resize"
    document.body.style.userSelect = "none"
  }, [])

  return (
    <div
      className="ide-workspace"
      style={{
        display: "grid",
        gridTemplateColumns: "var(--sidebar-width, 248px) minmax(0, 1fr) 360px",
        gridTemplateRows:
          `calc((100% - ${HANDLE}px) * ${footerSplit.ratio}) ` +
          `${HANDLE}px minmax(0, 1fr)`,
        minHeight: 0,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <aside
        className="ide-workspace-sidebar"
        style={{ gridRow: 1, gridColumn: 1 }}
      >
        {props.sidebar}
      </aside>

      <main
        className="ide-workspace-main"
        style={{
          gridRow: 1,
          gridColumn: 2,
          display: "grid",
          gridTemplateRows:
            `calc((100% - ${HANDLE}px) * ${mainSplit.ratio}) ` +
            `${HANDLE}px minmax(0, 1fr)`,
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        <section
          className="ide-workspace-code"
          style={{ gridRow: 1, gridColumn: 1 }}
        >
          <EditorPreferencesControls />
          {props.code}
        </section>

        <VerticalSplitHandle
          ariaLabel="Resize editor and agent panel"
          onPointerDown={mainSplit.onHandlePointerDown}
          onDoubleClick={mainSplit.onHandleDoubleClick}
          onKeyDown={mainSplit.onHandleKeyDown}
          style={{ gridRow: 2, gridColumn: 1 }}
        />

        <section
          className="ide-workspace-prompt"
          style={{ gridRow: 3, gridColumn: 1 }}
        >
          {props.prompt}
        </section>
      </main>

      <aside
        ref={rightRef}
        className="ide-workspace-execution"
        style={{ gridRow: 1, gridColumn: 3 }}
      >
        <section className="ide-workspace-execution-stream">
          {props.execution}
        </section>
        <div
          className="ide-right-resize"
          onMouseDown={onDown}
          role="separator"
          aria-orientation="horizontal"
          aria-label="Resize review panel"
        />
        <section className="ide-workspace-review">{props.review}</section>
      </aside>

      <VerticalSplitHandle
        ariaLabel="Resize terminal panel"
        onPointerDown={footerSplit.onHandlePointerDown}
        onDoubleClick={footerSplit.onHandleDoubleClick}
        onKeyDown={footerSplit.onHandleKeyDown}
        style={{ gridRow: 2, gridColumn: "1 / -1" }}
      />

      <footer
        className="ide-workspace-bottom"
        style={{ gridRow: 3, gridColumn: "1 / -1" }}
      >
        <section>{props.terminal}</section>
      </footer>
      <SidebarResizer />
    </div>
  )
}
