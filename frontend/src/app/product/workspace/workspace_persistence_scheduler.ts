export class WorkspacePersistenceScheduler {
  private pending: Promise<void> = Promise.resolve()

  private timer:
    ReturnType<typeof setTimeout> | null = null

  reset(): void {
    this.pending =
      Promise.resolve()

    if (this.timer) {
      clearTimeout(this.timer)
      this.timer = null
    }
  }

  schedule(
    task: () => Promise<void>,
  ): void {
    if (this.timer) {
      clearTimeout(this.timer)
    }

    this.timer =
      setTimeout(
        () => {
          this.timer = null

          this.pending =
            this.pending
              .catch(
                () => undefined,
              )
              .then(
                task,
              )
              .catch(
                () => undefined,
              )
        },
        1200,
      )
  }

  flush(
    task: () => Promise<void>,
  ): Promise<void> {
    this.pending =
      this.pending
        .catch(
          () => undefined,
        )
        .then(
          task,
        )
        .catch(
          () => undefined,
        )

    return this.pending
  }
}
