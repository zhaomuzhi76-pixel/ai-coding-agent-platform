import type {
  PlatformDomainInfo,
  PlatformModelOption,
} from "../../../core/contracts/platform"

export function PlatformModelPicker(props: {
  models: PlatformModelOption[]
  value: string
  disabled?: boolean
  onChange: (value: string) => void
}) {
  return (
    <label className="picker">
      <span className="muted">模型</span>
      <select
        value={props.value}
        disabled={props.disabled}
        onChange={(e) => props.onChange(e.target.value)}
      >
        {props.models.map((m) => (
          <option key={m.model} value={m.model}>
            {m.display_name} · {m.provider}
          </option>
        ))}
      </select>
    </label>
  )
}

export function PlatformDomainPicker(props: {
  domains: PlatformDomainInfo[]
  value: string
  disabled?: boolean
  onChange: (value: string) => void
}) {
  return (
    <label className="picker">
      <span className="muted">领域</span>
      <select
        value={props.value}
        disabled={props.disabled}
        onChange={(e) => props.onChange(e.target.value)}
      >
        {props.domains.map((d) => (
          <option key={d.name} value={d.name}>
            {d.name} ({d.entity_types.join("/")})
          </option>
        ))}
      </select>
    </label>
  )
}
