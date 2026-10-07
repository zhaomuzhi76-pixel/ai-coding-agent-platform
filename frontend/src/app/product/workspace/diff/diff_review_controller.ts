import {
  DiffReviewStore,
} from "./diff_review_store"

import type {
  DiffChange,
} from "./diff_review_contract"

export class DiffReviewController {
  readonly store: DiffReviewStore

  constructor(
    store: DiffReviewStore =
      new DiffReviewStore(),
  ) {
    this.store = store
  }

  getSnapshot() {
    return this.store.getSnapshot()
  }

  load(
    changes: readonly DiffChange[],
  ): void {
    this.store.dispatch({
      type: "load",
      changes,
    })
  }

  start(): void {
    this.store.dispatch({
      type: "start",
    })
  }

  approve(): void {
    this.store.dispatch({
      type: "approve",
    })
  }

  reject(): void {
    this.store.dispatch({
      type: "reject",
    })
  }

  close(): void {
    this.store.dispatch({
      type: "close",
    })
  }

  reset(): void {
    this.store.dispatch({
      type: "reset",
    })
  }
}
