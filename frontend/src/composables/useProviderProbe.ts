// Provider 临时链路探测 hook（不落盘）
import { useState } from 'react';

export interface ProbeModel {
  id: string;
  display: string;
}

export interface ProbeResult {
  ok: boolean;
  latency_ms?: number;
  error?: string;
  model_count?: number;
  models?: ProbeModel[];
}

export interface ProbePayload {
  kind: string;
  base_url: string;
  api_key?: string;
  existing_id?: string;
}

export function useProviderProbe() {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<ProbeResult | null>(null);

  const probe = async (payload: ProbePayload): Promise<ProbeResult> => {
    setTesting(true);
    setResult(null);
    try {
      const res = await fetch('/api/model-registry/providers/probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      // 后端可能返回非 JSON（500 HTML），做降级
      const text = await res.text();
      let data: ProbeResult;
      try {
        data = JSON.parse(text);
      } catch {
        data = { ok: false,
                 error: `HTTP ${res.status}: ${text.slice(0, 200)}` };
      }
      setResult(data);
      return data;
    } catch (e) {
      const err: ProbeResult = { ok: false, error: (e as Error).message };
      setResult(err);
      return err;
    } finally {
      setTesting(false);
    }
  };

  const reset = () => setResult(null);

  return { testing, result, probe, reset };
}
