import "./editor_surface.css"
import { useRef } from "react"
import type { UIEvent } from "react"
import type { EditorSurfaceProps } from "./editor_surface_contract"
import { useEditorSurfaceController } from "./editor_surface_controller"
import { EditorDiffView } from "./editor_diff_view"

export type { EditorSurfaceProps } from "./editor_surface_contract"

export function EditorSurface(props: EditorSurfaceProps) {
  const {
    document,
    editorRef,
    gutterRef,
    lines,
    editable,
    saveDisabled,
    status,
    onChange,
    onKeyDown,
    onScroll,
  } = useEditorSurfaceController(props)
  const previewRef = useRef<HTMLPreElement | null>(null)
  const activeFile = props.activeFile
  const pending = props.pendingChange ?? null

  function handleScroll(event: UIEvent<HTMLTextAreaElement>) {
    const textarea = event.currentTarget
    if (previewRef.current) {
      previewRef.current.scrollTop = textarea.scrollTop
      previewRef.current.scrollLeft = textarea.scrollLeft
    }
    onScroll(event)
  }

  return (
    <section className="workspace-editor" data-testid="workspace-editor">
      <header className="workspace-editor__header">
        <div className="workspace-editor__file">
          <span className="workspace-editor__file-icon" aria-hidden="true">◈</span>
          <strong title={activeFile ?? ""}>
            {activeFile ?? "No file selected"}
          </strong>
          {pending ? (
            <span className="workspace-editor__diff-badge">DIFF</span>
          ) : null}
          {!pending && document.dirty ? (
            <span
              className="workspace-editor__unsaved-badge"
              title="有未保存的修改"
            >
              ● 未保存
            </span>
          ) : null}
        </div>
        <div className="workspace-editor__actions">
          {pending ? (
            <>
              <button
                type="button"
                className="workspace-editor__accept"
                onClick={() => pending.onApprove?.()}
              >
                ✓ Accept
              </button>
              <button
                type="button"
                className="workspace-editor__reject"
                onClick={() => pending.onReject?.()}
              >
                ✕ Reject
              </button>
            </>
          ) : (
            <>
              <span className="workspace-editor__status" role="status">{status}</span>
              <button
                type="button"
                className={
                  "workspace-editor__save-btn"
                  + (document.dirty ? " is-dirty" : "")
                  + (document.saving ? " is-saving" : "")
                }
                disabled={saveDisabled}
                onClick={() => void document.save()}
              >
                {document.saving
                  ? "Saving..."
                  : document.dirty
                    ? "● Save"
                    : "Save"}
              </button>
            </>
          )}
        </div>
      </header>

      <div className="workspace-editor__body">
        {pending ? (
          <EditorDiffView before={pending.before} after={pending.after} />
        ) : document.loading ? (
          <div className="workspace-editor__empty">
            <strong>Loading file...</strong>
            <span>{activeFile}</span>
          </div>
        ) : document.loadError ? (
          <div className="workspace-editor__empty" role="alert">
            <strong>Unable to load file</strong>
            <span>{document.loadError}</span>
          </div>
        ) : !activeFile ? (
          <div className="workspace-editor__empty">
            <strong>Select a file</strong>
            <span>Choose a file from the project tree.</span>
          </div>
        ) : (
          <div className="workspace-editor__code">
            <div ref={gutterRef} className="workspace-editor__gutter" aria-hidden="true">
              {lines.map(number => <div key={number}>{number}</div>)}
            </div>
            <div className="workspace-editor__content-layer">
              <pre ref={previewRef} className="workspace-editor__preview" aria-hidden="true">
                {document.content}
              </pre>
              <textarea
                ref={editorRef}
                className="workspace-editor__content"
                data-testid="workspace-editor-content"
                aria-label={`Editor ${activeFile}`}
                value={document.content}
                readOnly={!editable}
                spellCheck={false}
                onChange={onChange}
                onKeyDown={onKeyDown}
                onScroll={handleScroll}
              />
            </div>
          </div>
        )}
        {document.saveError && !pending ? (
          <div role="alert" className="workspace-editor__error">
            {document.saveError}
          </div>
        ) : null}
      </div>
    </section>
  )
}
