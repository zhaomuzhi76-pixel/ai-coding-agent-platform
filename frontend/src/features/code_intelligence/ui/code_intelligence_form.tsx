import { useState } from "react"
import type {
  CodeIntelligenceOperation,
  CodeIntelligenceRequest,
} from "../../../core/api/code_intelligence_api"

interface CodeIntelligenceFormProps {
  busy: boolean
  onSubmit: (request: CodeIntelligenceRequest) => void
}

const operations: CodeIntelligenceOperation[] = [
  "summary",
  "project",
  "file",
  "analysis",
  "impact",
  "context",
  "index",
]

export function CodeIntelligenceForm(
  props: CodeIntelligenceFormProps,
) {
  const [operation, setOperation] =
    useState<CodeIntelligenceOperation>("summary")
  const [query, setQuery] = useState("inspect project")
  const [workspace, setWorkspace] = useState(".")
  const [path, setPath] = useState("")

  const needsPath =
    operation === "file" || operation === "impact"

  return (
    <form
      className="intelligence-form"
      onSubmit={event => {
        event.preventDefault()
        props.onSubmit({
          query,
          workspace,
          path: path || undefined,
          metadata: { operation },
        })
      }}
    >
      <label>
        Operation
        <select
          value={operation}
          disabled={props.busy}
          onChange={event =>
            setOperation(
              event.target.value as CodeIntelligenceOperation,
            )
          }
        >
          {operations.map(item => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label>
        Query
        <input
          value={query}
          disabled={props.busy}
          onChange={event =>
            setQuery(event.target.value)
          }
          placeholder="inspect project"
        />
      </label>

      <label>
        Workspace
        <input
          value={workspace}
          disabled={props.busy}
          onChange={event =>
            setWorkspace(event.target.value)
          }
          placeholder="."
        />
      </label>

      <label>
        Path
        <input
          value={path}
          disabled={props.busy}
          onChange={event =>
            setPath(event.target.value)
          }
          placeholder={
            needsPath
              ? "backend/example.py"
              : "optional"
          }
        />
      </label>

      <button
        type="submit"
        disabled={
          props.busy
          || !query.trim()
          || !workspace.trim()
          || (needsPath && !path.trim())
        }
      >
        {props.busy
          ? "Inspecting..."
          : "Run Inspection"}
      </button>
    </form>
  )
}
