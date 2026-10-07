import type {
  ApplicationPlugin,
  PluginRegistryContract,
} from "./plugin_contract"

export class PluginRegistry
  implements PluginRegistryContract {
  private readonly plugins =
    new Map<string, ApplicationPlugin>()

  register(
    plugin: ApplicationPlugin,
  ): void {
    if (
      !plugin.id.trim()
      || !plugin.title.trim()
      || !plugin.render
    ) {
      throw new Error(
        "invalid application plugin",
      )
    }

    if (this.plugins.has(plugin.id)) {
      throw new Error(
        `application plugin already registered: ${plugin.id}`,
      )
    }

    this.plugins.set(
      plugin.id,
      plugin,
    )
  }

  resolve(
    id: string,
  ): ApplicationPlugin | null {
    return this.plugins.get(id) ?? null
  }

  all(): readonly ApplicationPlugin[] {
    return [...this.plugins.values()]
  }

  ready(): boolean {
    return [...this.plugins.values()].every(
      plugin =>
        Boolean(
          plugin.id.trim()
          && plugin.title.trim()
          && plugin.render,
        ),
    )
  }
}
