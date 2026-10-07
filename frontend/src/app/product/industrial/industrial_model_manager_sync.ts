import {
  ModelCatalog,
} from "../../../core/models/model_catalog"


interface CurrentModel {
  provider: string
  model: string
  base_url: string
}


export function matchModelCatalog(
  catalog: ModelCatalog,
  current: CurrentModel,
): ModelCatalog | null {

  const match =
    catalog
      .list()
      .find(
        profile =>
          profile.provider === current.provider
          &&
          profile.model === current.model
          &&
          profile.base_url === current.base_url,
      )

  if (!match) {
    return null
  }

  if (match.id === catalog.active()?.id) {
    return null
  }

  return new ModelCatalog(
    catalog.list(),
    match.id,
  )
}
