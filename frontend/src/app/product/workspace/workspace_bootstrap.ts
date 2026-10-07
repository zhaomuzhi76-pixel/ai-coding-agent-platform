export class WorkspaceBootstrap {

  private started =
    false


  async start() {

    if (this.started) {
      return
    }

    this.started = true

    return
  }
}
