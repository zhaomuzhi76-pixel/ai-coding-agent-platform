import type {
  DiffReviewAction,
  DiffReviewSnapshot,
} from "./diff_review_contract"

export class DiffReviewStore {
  private state: DiffReviewSnapshot = {
    changes: [],
    status: "idle",
    reviewing: false,
  }

  getSnapshot(): DiffReviewSnapshot {
    return this.state
  }

  dispatch(
    action: DiffReviewAction,
  ): void {
    switch (action.type) {
      case "load":
        this.state = {
          changes: [...action.changes],
          status:
            action.changes.length > 0
              ? "pending"
              : "idle",
          reviewing: false,
        }
        return

      case "start":
        this.state = {
          ...this.state,
          status:
            this.state.changes.length > 0
              ? "pending"
              : "idle",
          reviewing:
            this.state.changes.length > 0,
        }
        return

      case "approve":
        if (!this.state.reviewing) {
          return
        }
        this.state = {
          ...this.state,
          status: "approved",
          reviewing: false,
        }
        return

      case "reject":
        if (!this.state.reviewing) {
          return
        }
        this.state = {
          ...this.state,
          status: "rejected",
          reviewing: false,
        }
        return

      case "close":
        this.state = {
          ...this.state,
          reviewing: false,
        }
        return

      case "reset":
        this.state = {
          changes: [],
          status: "idle",
          reviewing: false,
        }
        return
    }
  }
}

export function reduceDiffReview(
  state: DiffReviewSnapshot,
  action: DiffReviewAction,
): DiffReviewSnapshot {
  const store = new DiffReviewStore()
  store.dispatch({
    type: "load",
    changes: state.changes,
  })
  store.dispatch(action)
  return store.getSnapshot()
}
