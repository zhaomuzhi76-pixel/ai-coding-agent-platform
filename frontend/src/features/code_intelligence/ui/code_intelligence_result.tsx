import type {
  CodeIntelligenceResult,
} from "../../../core/api/code_intelligence_api"

interface CodeIntelligenceResultProps {
  result: CodeIntelligenceResult | null
  error: string | null
}

export function CodeIntelligenceResultView(
  props: CodeIntelligenceResultProps,
) {
  if (props.error) {
    return (
      <section className="intelligence-result intelligence-result-error">
        <strong>Inspection failed</strong>
        <span>{props.error}</span>
      </section>
    )
  }

  if (!props.result) {
    return (
      <section className="intelligence-result intelligence-result-empty">
        <span>No intelligence result yet.</span>
      </section>
    )
  }

  return (
    <section className="intelligence-result">
      <header>
        <span>RESULT</span>
        <strong>{props.result.name}</strong>
      </header>

      <div className="intelligence-result-meta">
        <span>
          Findings: {props.result.findings.length}
        </span>
        <span>
          Ready: {String(props.result.ready)}
        </span>
      </div>

      <pre>
        {JSON.stringify(
          props.result,
          null,
          2,
        )}
      </pre>
    </section>
  )
}
