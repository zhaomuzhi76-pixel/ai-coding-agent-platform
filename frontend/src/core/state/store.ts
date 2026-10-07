export type Listener = () => void

export interface ReadonlyStore<T> {
  getSnapshot(): T
  subscribe(listener: Listener): () => void
}

export class Store<T> implements ReadonlyStore<T> {
  private snapshot: T
  private readonly listeners = new Set<Listener>()

  constructor(initial: T) {
    this.snapshot = initial
  }

  getSnapshot(): T {
    return this.snapshot
  }

  setSnapshot(next: T): void {
    this.snapshot = next
    for (const listener of this.listeners) {
      listener()
    }
  }

  update(
    updater: (current: T) => T,
  ): void {
    this.setSnapshot(
      updater(this.snapshot),
    )
  }

  subscribe(
    listener: Listener,
  ): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }
}
