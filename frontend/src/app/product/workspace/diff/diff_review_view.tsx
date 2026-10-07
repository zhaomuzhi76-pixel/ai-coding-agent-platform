import "./diff_review.css"

import {
  useEffect,
  useRef,
  useState,
} from "react"

import {
  DiffReviewController,
} from "./diff_review_controller"

import {
  DiffReviewLineView,
} from "./diff_review_line_view"

import type {
  DiffChange,
  DiffReviewStatus,
} from "./diff_review_contract"

export interface DiffReviewViewProps {
  changes?: readonly DiffChange[]
  onOpenFile?: (file: string) => void
  onApprove?: (changes: readonly DiffChange[]) => void
  onReject?: (changes: readonly DiffChange[]) => void
}

function statusLabel(status: DiffReviewStatus): string {
  switch (status) {
    case "pending": return "PENDING"
    case "approved": return "APPROVED"
    case "rejected": return "REJECTED"
    default: return "IDLE"
  }
}

function sameChanges(
  left: readonly DiffChange[],
  right: readonly DiffChange[],
): boolean {
  return (
    left.length === right.length
    && left.every(
      (item, index) =>
        item.file === right[index]?.file
        && item.before === right[index]?.before
        && item.after === right[index]?.after,
    )
  )
}

export function DiffReviewView(props: DiffReviewViewProps) {
  const [controller] = useState(() => new DiffReviewController())
  const [, rerender] = useState(0)
  const loadedChanges = useRef<readonly DiffChange[]>([])

  useEffect(() => {
    const changes = props.changes ?? []
    if (sameChanges(loadedChanges.current, changes)) return
    controller.load(changes)
    loadedChanges.current = [...changes]
    rerender(v => v + 1)
  }, [controller, props.changes])

  const snapshot = controller.getSnapshot()

  const update = (action: () => void) => {
    action()
    rerender(v => v + 1)
  }

  const onApprove = () => {
    const changes = snapshot.changes
    update(() => controller.approve())
    props.onApprove?.(changes)
  }

  const onReject = () => {
    const changes = snapshot.changes
    update(() => controller.reject())
    props.onReject?.(changes)
  }

  return (
    <section aria-label="Diff Review" className="diff-review">
      <header className="diff-review__header">
        <div>
          <strong>Diff Review</strong>
          <span>{snapshot.changes.length} changes</span>
        </div>
        <span className={`diff-review__status diff-review__status--${snapshot.status}`}>
          {statusLabel(snapshot.status)}
        </span>
      </header>

      <div className="diff-review__body">
        {snapshot.changes.length === 0 ? (
          <div className="diff-review__empty">
            No changes pending review
          </div>
        ) : (
          snapshot.changes.map((change, index) => (
            <article key={`${change.file}-${index}`} className="diff-review__change">
              <header>
                <strong>{change.file}</strong>
                {props.onOpenFile && (
                  <button
                    type="button"
                    onClick={() => props.onOpenFile?.(change.file)}
                  >
                    Open
                  </button>
                )}
              </header>
              <DiffReviewLineView
                before={change.before}
                after={change.after}
              />
            </article>
          ))
        )}
      </div>

      <footer className="diff-review__actions">
        <button
          type="button"
          disabled={snapshot.changes.length === 0 || snapshot.reviewing}
          onClick={() => update(() => controller.start())}
        >
          Review
        </button>
        <button type="button" disabled={!snapshot.reviewing} onClick={onApprove}>
          Approve
        </button>
        <button type="button" disabled={!snapshot.reviewing} onClick={onReject}>
          Reject
        </button>
        <button
          type="button"
          disabled={!snapshot.reviewing}
          onClick={() => update(() => controller.close())}
        >
          Close
        </button>
        <button
          type="button"
          disabled={snapshot.reviewing || snapshot.changes.length === 0}
          onClick={() => update(() => controller.reset())}
        >
          Reset
        </button>
      </footer>
    </section>
  )
}
