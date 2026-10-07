import type { PlatformStore } from "../platform_store"
type Internals = Pick<PlatformStore, never> & {
  patch(partial: any): void
  gateway: any
  state: any
}

export async function loadCatalogImpl(store: Internals): Promise<void> {

      store.patch({ phase: "loading_catalog", error: null })
      try {
        const [models, domains, history] = await Promise.all([
          store.gateway.listModels(),
          store.gateway.listDomains(),
          store.gateway.listProposals().catch(
            () => ({ items: [] as typeof store.state.proposals, count: 0 })),
        ])
        const selectedModel =
          store.state.selectedModel || models[0]?.model || ""
        const selectedDomain =
          store.state.selectedDomain || domains[0]?.name || ""
        store.patch({
          phase: "ready",
          models,
          domains,
          proposals: history.items,
          selectedModel,
          selectedDomain,
        })
      } catch (error) {
        store.patch({
          phase: "error",
          error: String(error),
        })
      }
  
}
