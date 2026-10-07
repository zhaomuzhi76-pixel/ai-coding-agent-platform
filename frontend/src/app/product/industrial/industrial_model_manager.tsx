import type { Locale } from "../../../core/i18n/locale"

import type {
  ModelProfile,
} from "../../../core/models/model_catalog"

import {
  industrialText,
} from "./industrial_copy"

import {
  IndustrialModelCard,
} from "./industrial_model_card"

import {
  IndustrialModelEditor,
} from "./industrial_model_editor"

import {
  useIndustrialModelManagerState,
} from "./industrial_model_manager_state"


interface Props {
  locale: Locale
  current: {
    provider:string
    model:string
    base_url:string
  }
  expanded:boolean
  onSelect(profile:ModelProfile):void
}


export function IndustrialModelManager(
  props:Props,
) {

  const state =
    useIndustrialModelManagerState({
      current: props.current,
      onSelect: props.onSelect,
    })


  function select(
    profile:ModelProfile,
  ) {
    const next =
      new (state.catalog.constructor as any)(
        state.catalog.list(),
        profile.id,
      )

    state.commit(next)
    props.onSelect(profile)
  }


  function edit(
    profile:ModelProfile,
  ) {
    state.setEditingId(profile.id)

    state.setForm({
      label:profile.label,
      provider:profile.provider,
      model:profile.model,
      base_url:profile.base_url,
      api_key:profile.api_key,
    })
  }


  function remove(
    id:string,
  ){
    const next =
      state.catalog

    next.remove(id)

    state.commit(next)

    const active =
      next.active()

    if(active){
      props.onSelect(active)
    }
  }


  function save(){
    state.setError(null)
  }


  return (
    <section className={
      props.expanded
      ?
      "industrial-model-manager industrial-model-manager--expanded"
      :
      "industrial-model-manager"
    }>

      <strong>
        {industrialText(
          props.locale,
          "models",
        )}
      </strong>


      {props.expanded &&
      <>
        <div>
          {
            state.catalog
            .list()
            .map(profile =>
              <IndustrialModelCard
                key={profile.id}
                profile={profile}
                active={
                  profile.id ===
                  state.active?.id
                }
                onSelect={select}
                onEdit={edit}
                onRemove={remove}
              />
            )
          }
        </div>


        <IndustrialModelEditor
          locale={props.locale}
          form={state.form}
          editing={
            state.editingId !== null
          }
          error={state.error}
          onChange={
            state.setForm
          }
          onSave={save}
          onReset={() =>
            state.setEditingId(null)
          }
        />

      </>
      }

    </section>
  )
}
