import type { Locale } from "../../../core/i18n/locale"
import type {
  ModelSelection,
} from "../../../core/contracts/model"
import type { ModelForm } from "./industrial_model_manager_support"
import { industrialText } from "./industrial_copy"

interface IndustrialModelEditorProps {
  locale: Locale
  form: ModelForm
  editing: boolean
  error: string | null
  onChange(form: ModelForm): void
  onSave(): void
  onReset(): void
}

export function IndustrialModelEditor(
  props: IndustrialModelEditorProps,
) {
  const set =
    <K extends keyof ModelForm>(
      key: K,
      value: ModelForm[K],
    ) =>
      props.onChange({
        ...props.form,
        [key]: value,
      })

  return (
    <div className="industrial-model-editor">
      <div className="industrial-model-editor__title">
        <strong>
          {props.editing
            ? industrialText(
                props.locale,
                "editModel",
              )
            : industrialText(
                props.locale,
                "addModel",
              )}
        </strong>
        <button
          type="button"
          onClick={props.onReset}
        >
          +
        </button>
      </div>

      <div className="industrial-model-editor__grid">
        <label>
          <span>
            {industrialText(
              props.locale,
              "provider",
            )}
          </span>
          <select
            value={props.form.provider}
            onChange={event =>
              set(
                "provider",
                event.target.value as ModelSelection["provider"],
              )
            }
          >
            <option value="ollama">Ollama</option>
            <option value="openai_compatible">
              OpenAI Compatible
            </option>
          </select>
        </label>

        <label>
          <span>
            {industrialText(
              props.locale,
              "modelName",
            )}
          </span>
          <input
            value={props.form.model}
            onChange={event =>
              set("model", event.target.value)
            }
          />
        </label>

        <label>
          <span>Label</span>
          <input
            value={props.form.label}
            onChange={event =>
              set("label", event.target.value)
            }
          />
        </label>

        <label>
          <span>
            {industrialText(
              props.locale,
              "baseUrl",
            )}
          </span>
          <input
            value={props.form.base_url}
            onChange={event =>
              set(
                "base_url",
                event.target.value,
              )
            }
          />
        </label>

        <label>
          <span>
            {industrialText(
              props.locale,
              "apiKey",
            )}
          </span>
          <input
            type="password"
            value={props.form.api_key}
            onChange={event =>
              set(
                "api_key",
                event.target.value,
              )
            }
          />
        </label>
      </div>

      {props.error && (
        <div className="industrial-inline-error">
          {props.error}
        </div>
      )}

      <button
        className="industrial-primary-action"
        type="button"
        onClick={props.onSave}
      >
        {industrialText(
          props.locale,
          "saveModel",
        )}
      </button>
    </div>
  )
}
