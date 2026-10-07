export type DiffReviewStatus =
  | "idle"
  | "pending"
  | "approved"
  | "rejected"

export interface DiffChange {
  file: string
  before: string
  after: string
}

export interface DiffReviewSnapshot {
  changes: readonly DiffChange[]
  status: DiffReviewStatus
  reviewing: boolean
}

export type DiffReviewAction =
  | {
      type: "load"
      changes: readonly DiffChange[]
    }
  | {
      type: "start"
    }
  | {
      type: "approve"
    }
  | {
      type: "reject"
    }
  | {
      type: "close"
    }
  | {
      type: "reset"
    }
