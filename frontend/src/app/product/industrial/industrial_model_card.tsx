import type { ModelProfile } from "../../../core/models/model_catalog"

interface IndustrialModelCardProps {
  profile: ModelProfile
  active: boolean
  onSelect(profile: ModelProfile): void
  onEdit(profile: ModelProfile): void
  onRemove(id: string): void
}

export function IndustrialModelCard(
  props: IndustrialModelCardProps,
) {
  return (
    <div
      className={
        props.active
          ? "industrial-model-card industrial-model-card--active"
          : "industrial-model-card"
      }
    >
      <button
        type="button"
        className="industrial-model-card__main"
        onClick={() => props.onSelect(props.profile)}
      >
        <strong>{props.profile.label}</strong>
        <span>
          {props.profile.provider}
          {" · "}
          {props.profile.model}
        </span>
        <small>{props.profile.base_url}</small>
      </button>

      <div className="industrial-model-card__actions">
        <button
          type="button"
          onClick={() => props.onEdit(props.profile)}
        >
          Edit
        </button>
        <button
          type="button"
          onClick={() => props.onRemove(props.profile.id)}
        >
          Remove
        </button>
      </div>
    </div>
  )
}
