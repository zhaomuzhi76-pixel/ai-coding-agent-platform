import React, { useEffect, useState } from 'react';
import type {
  CreateProviderPayload, ProviderCard as PC, ProviderKindSpec,
} from '../../types/model_registry';
import { useProviderProbe } from '../../composables/useProviderProbe';

interface Props {
  open: boolean;
  editing: PC | null;
  onClose: () => void;
  onSubmit: (p: CreateProviderPayload) => void;
  onDelete: (id: string) => void;
}

const EMPTY: CreateProviderPayload = {
  id: '', name: '', kind: 'ollama', base_url: '', api_key: '', enabled: true,
};

const KIND_ALIAS: Record<string, string> = {
  cloud: 'dashscope', local: 'ollama', 'ollama-local': 'ollama',
};

function normalizeKind(k: string, kinds: ProviderKindSpec[]): string {
  if (!k) return kinds[0]?.value ?? 'ollama';
  if (kinds.some((x) => x.value === k)) return k;
  const m = KIND_ALIAS[k];
  if (m && kinds.some((x) => x.value === m)) return m;
  return kinds[0]?.value ?? 'ollama';
}

function fillBaseUrl(baseUrl: string, kind: string): string {
  const base = (baseUrl || '').trim().replace(/\/+$/, '');
  if (kind === 'dashscope' && /dashscope\.aliyuncs\.com$/.test(base)) {
    return base + '/compatible-mode/v1';
  }
  return base;
}

// 官方模型名格式：小写字母/数字开头，可含 . - _ : / 大写
const MODEL_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:\/-]*$/;

export const ProviderDetailModal: React.FC<Props> = ({
  open, editing, onClose, onSubmit, onDelete,
}) => {
  const [form, setForm] = useState<CreateProviderPayload>(EMPTY);
  const [kinds, setKinds] = useState<ProviderKindSpec[]>([]);
  const [testedKey, setTestedKey] = useState('');
  const [saveAsNew, setSaveAsNew] = useState(false);
  const { testing, result, probe, reset } = useProviderProbe();

  useEffect(() => {
    if (!open) return;
    fetch('/api/model-registry/provider-kinds')
      .then((r) => (r.ok ? r.json() : []))
      .then((ks: ProviderKindSpec[]) => {
        setKinds(ks);
        if (editing) {
          setForm({
            id: editing.id,
            name: editing.name,
            kind: normalizeKind(editing.kind || 'ollama', ks),
            base_url: editing.base_url,
            api_key: '',
            enabled: editing.enabled,
          });
        } else {
          setForm(EMPTY);
        }
      })
      .catch(() => setKinds([]));
    setTestedKey('');
    setSaveAsNew(false);
    reset();
  }, [open, editing]);

  if (!open) return null;

  const groups = {
    local: kinds.filter((k) => k.category === 'local'),
    cloud: kinds.filter((k) => k.category === 'cloud'),
  };
  const currentKind = kinds.find((k) => k.value === form.kind);
  const isEdit = !!editing && !saveAsNew;
  const needsKey = currentKind?.needs_key ?? false;
  const idHint: string = (currentKind as any)?.id_hint ?? '';
  const idValid = MODEL_ID_RE.test(form.id.trim());

  const probeKey = `${form.kind}|${form.base_url}|${form.api_key || ''}|${editing?.id || ''}`;
  const passedTest = testedKey === probeKey && testedKey !== '';
  const canSave = passedTest && !!form.id && idValid && !!form.base_url;

  const update = <K extends keyof CreateProviderPayload>(
    k: K, v: CreateProviderPayload[K],
  ) => setForm((f) => ({ ...f, [k]: v }));

  const onKindChange = (v: string) => {
    const spec = kinds.find((k) => k.value === v);
    setForm((f) => ({
      ...f,
      kind: v,
      base_url: spec && !f.base_url ? spec.default_base_url : f.base_url,
      name: f.name || (spec ? spec.label : ''),
    }));
    setTestedKey('');
  };

  const onTest = async () => {
    const r = await probe({
      kind: form.kind,
      base_url: form.base_url,
      api_key: form.api_key || '',
      existing_id: editing?.id || '',
    });
    if (r.ok) setTestedKey(probeKey);
  };

  const handleSave = () => {
    onSubmit({ ...form, base_url: fillBaseUrl(form.base_url, form.kind) });
  };

  return (
    <div className="mr-modal-mask" onClick={onClose}>
      <div className="mr-modal" onClick={(e) => e.stopPropagation()}>
        <h3>
          {saveAsNew ? '另存为新的 Provider'
           : isEdit ? '编辑 Provider' : '新增 Provider'}
        </h3>

        <div className="mr-note">
          ID 填<b>官方模型名</b>（手填，不选），如
          <code>qwen-max</code> / <code>gpt-4o</code> /
          <code>claude-3-5-sonnet-20241022</code>，
          后端 <code>/v1/models</code> 靠它匹配。
        </div>

        <label>类型</label>
        <select value={form.kind} onChange={(e) => onKindChange(e.target.value)}>
          <optgroup label="本地部署">
            {groups.local.map((k) => (
              <option key={k.value} value={k.value}>{k.label}</option>
            ))}
          </optgroup>
          <optgroup label="云端 API">
            {groups.cloud.map((k) => (
              <option key={k.value} value={k.value}>{k.label}</option>
            ))}
          </optgroup>
        </select>

        <label>模型 ID（手动填写官方模型名）</label>
        <input value={form.id} disabled={isEdit}
               onChange={(e) => update('id', e.target.value)}
               placeholder={idHint || 'qwen-max'}
               autoComplete="off"
               spellCheck={false}
               className={form.id && !idValid ? 'mr-input-invalid' : ''} />
        {form.id && !idValid && (
          <div className="mr-field-error">
            格式不合法：不能含空格、中文或特殊字符
          </div>
        )}
        {idHint && !form.id && (
          <div className="mr-field-hint">{idHint}</div>
        )}

        <label>显示名称（可改）</label>
        <input value={form.name || ''}
               onChange={(e) => update('name', e.target.value)} />

        <label>Base URL</label>
        <input value={form.base_url}
               onChange={(e) => update('base_url', e.target.value)}
               placeholder={currentKind?.default_base_url || 'https://...'} />

        {needsKey && (
          <>
            <label>API Key</label>
            <input type="password" value={form.api_key || ''}
                   onChange={(e) => update('api_key', e.target.value)}
                   placeholder="sk-..." />
          </>
        )}

        <div className="mr-probe-row">
          <button className="mr-probe-btn" onClick={onTest} disabled={testing}>
            {testing ? '测试中…' : '测试连通性'}
          </button>
          {result && result.ok && (
            <span className="mr-probe-ok">
              ✅ 通过 · {result.latency_ms}ms · {result.model_count} 模型
            </span>
          )}
          {result && !result.ok && (
            <span className="mr-probe-err">❌ {result.error}</span>
          )}
        </div>

        <div className="mr-modal-actions">
          {isEdit && (
            <>
              <button className="danger" onClick={() => onDelete(form.id)}>
                删除
              </button>
              <button onClick={() => {
                setSaveAsNew(true);
                setForm((f) => ({ ...f, id: f.id + '-copy', api_key: '' }));
                setTestedKey('');
                reset();
              }}>另存为</button>
            </>
          )}
          <button onClick={onClose}>取消</button>
          <button className="primary" onClick={handleSave}
                  disabled={!canSave}
                  title={!canSave ? 'ID 合法 + 通过连通测试 才能保存' : ''}>
            保存
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProviderDetailModal;
