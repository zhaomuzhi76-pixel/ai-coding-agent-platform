import React, { useEffect, useState } from 'react';
import type { RoleCard as RC } from '../../types/model_registry';

interface BindPayload {
  role: string;
  primary: string;
  fallback: string | null;
}

interface TestResult {
  slot: string;
  model: string;
  provider?: string;
  ok: boolean;
  latency_ms?: number;
  error?: string;
}

interface Props {
  r: RC;
  onBind: (p: BindPayload) => void;
}

/** [OPT] 按 verified 分组 */
function _splitCandidates(
  cands: Array<{ value: string; label: string; group: string; verified?: boolean }>,
) {
  const yes: typeof cands = [];
  const no: typeof cands = [];
  for (const c of cands) (c.verified ? yes : no).push(c);
  return { yes, no };
}

export const RoleCard: React.FC<Props> = ({ r, onBind }) => {
  const [primary, setPrimary] = useState(r.primary);
  const [fallback, setFallback] = useState<string | null>(r.fallback);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult[] | null>(null);

  useEffect(() => {
    setPrimary(r.primary);
    setFallback(r.fallback);
  }, [r.primary, r.fallback]);

  const dirty = primary !== r.primary || fallback !== r.fallback;

  const handlePrimary = (v: string) => {
    setPrimary(v);
    if (v !== r.primary || fallback !== r.fallback) {
      onBind({ role: r.role, primary: v, fallback });
    }
  };
  const handleFallback = (v: string) => {
    const fb = v || null;
    setFallback(fb);
    if (primary !== r.primary || fb !== r.fallback) {
      onBind({ role: r.role, primary, fallback: fb });
    }
  };

  const runTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch(
        `/api/model-registry/roles/${encodeURIComponent(r.role)}/test`,
        { method: 'POST' },
      );
      const data = await res.json();
      setTestResult((data?.data ?? data).results ?? []);
    } catch (e) {
      setTestResult([{
        slot: 'error', model: '', ok: false,
        error: String(e),
      }]);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="mr-role-card">
      <div className="mr-role-header">
        <span className="mr-role-label">{r.label}</span>
        <span className="mr-role-key">{r.role}</span>
        <button className="mr-role-test-btn"
                onClick={runTest} disabled={testing}
                title="测试该角色配置的模型是否可用">
          {testing ? "…" : "测试"}
        </button>
      </div>
      <div className="mr-role-row">
        <label>Primary</label>
        <select value={primary} onChange={(e) => handlePrimary(e.target.value)}>
          {(() => {
            const { yes, no } = _splitCandidates(r.candidates)
            return (
              <>
                {yes.length > 0 && (
                  <optgroup label={`✅ 已验证（${yes.length}）`}>
                    {yes.map((c: any) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </optgroup>
                )}
                <optgroup label={`📋 全部模型（${no.length}）`}>
                  {no.map((c: any) => (
                    <option key={c.value} value={c.value}>[{c.group}] {c.label}</option>
                  ))}
                </optgroup>
              </>
            )
          })()}
        </select>
      </div>
      <div className="mr-role-row">
        <label>Fallback</label>
        <select value={fallback || ''} onChange={(e) => handleFallback(e.target.value)}>
          <option value="">-- none --</option>
          {(() => {
            const { yes, no } = _splitCandidates(r.candidates)
            return (
              <>
                {yes.length > 0 && (
                  <optgroup label={`✅ 已验证（${yes.length}）`}>
                    {yes.map((c: any) => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </optgroup>
                )}
                <optgroup label={`📋 全部模型（${no.length}）`}>
                  {no.map((c: any) => (
                    <option key={c.value} value={c.value}>[{c.group}] {c.label}</option>
                  ))}
                </optgroup>
              </>
            )
          })()}
        </select>
      </div>
      <div className={'mr-role-status' + (dirty ? '' : ' ok')}>
        {dirty ? <span>保存中…</span> : <span>✅ 已生效</span>}
      </div>
      {testResult && (
        <div className="mr-role-test-result">
          {testResult.map((t, i) => (
            <div key={i} className={t.ok ? 'ok' : 'err'}>
              {t.ok ? '✅' : '❌'} {t.slot}: {t.model}
              {t.latency_ms && ` · ${t.latency_ms}ms`}
              {t.error && <span className="mr-role-test-err"> · {t.error}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RoleCard;