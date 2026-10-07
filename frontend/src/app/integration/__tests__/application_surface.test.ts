import {
  describe,
  expect,
  it,
} from "vitest"
import {
  createApplicationPluginRegistry,
} from "../../plugins/application_plugins"
import {
  PluginRegistry,
} from "../../plugins/plugin_registry"

describe(
  "application plugin integration",
  () => {
    it("builds a ready registry", () => {
      const registry =
        createApplicationPluginRegistry()

      expect(
        registry,
      ).toBeInstanceOf(PluginRegistry)

      expect(
        registry.ready(),
      ).toBe(true)

      expect(
        registry.all().map(
          plugin => plugin.id,
        ),
      ).toEqual([
        "industrial-control-plane",
        "platform-workbench",
      ])
    })

    it("rejects duplicate plugin ownership", () => {
      const registry = new PluginRegistry()
      const plugin = {
        id: "test",
        title: "Test",
        render: () => null,
      }

      registry.register(plugin)

      expect(() =>
        registry.register(plugin),
      ).toThrow(
        "already registered",
      )
    })
  },
)
