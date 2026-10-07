// Agent 顶栏模型下拉：只显示已通过链路测试的模型
// 数据源: GET /api/model-registry/verified-models
import React, { useEffect, useState } from 'react';

export interface VerifiedModel {
  id: string;
  provider: string;
  display_name: string;
  label: string;
}

interface Props {
  value?: string;
  onChange?: (v: string) => void;
  className?: string;
  placeholder?: string;
}

export const VerifiedModelSelect: React.FC<Props> = ({
  value, onChange, className, placeholder,
}) => {
  const [models, setModels] = useState<VerifiedModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    let alive = true;
    fetch('/api/model-registry/verified-models')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((data: VerifiedModel[]) => { if (alive) setModels(data); })
      .catch((e) => { if (alive) setErr(String(e)); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  if (loading) return <div className="mr-vm mr-vm-hint">加载中…</div>;
  if (err) return <div className="mr-vm mr-vm-err">加载失败: {err}</div>;
  if (models.length === 0) {
    return (
      <div className="mr-vm mr-vm-hint">
        无已验证模型 · 请到配置中心测试连通性
      </div>
    );
  }

  return (
    <select
      className={'mr-vm-select' + (className ? ' ' + className : '')}
      value={value || (models[0] ? models[0].id : '')}
      onChange={(e) => onChange && onChange(e.target.value)}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {models.map((m) => (
        <option key={m.id} value={m.id}>
          {m.id} · {m.provider}
        </option>
      ))}
    </select>
  );
};

export default VerifiedModelSelect;
