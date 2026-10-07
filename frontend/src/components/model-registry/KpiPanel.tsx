import React, { useEffect, useState } from 'react';

interface UsageKPI {
  models_by_provider: Record<string, number>;
  avg_role_cost_per_1k: number;
  roles_routed: number;
  total_models: number;
  total_roles: number;
}

export const KpiPanel: React.FC = () => {
  const [kpi, setKpi] = useState<UsageKPI | null>(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    fetch('/api/model-registry/kpi/usage')
      .then((r) => r.json())
      .then(setKpi)
      .catch((e) => setErr(e.message));
  }, []);

  if (err) return <div className="mr-kpi-panel err">KPI 加载失败: {err}</div>;
  if (!kpi) return <div className="mr-kpi-panel">加载中…</div>;

  return (
    <div className="mr-kpi-panel">
      <div className="mr-kpi-block">
        <span className="label">Providers</span>
        <span className="val">{Object.keys(kpi.models_by_provider).length}</span>
      </div>
      <div className="mr-kpi-block">
        <span className="label">Models</span>
        <span className="val">{kpi.total_models}</span>
      </div>
      <div className="mr-kpi-block">
        <span className="label">Roles</span>
        <span className="val">{kpi.roles_routed}/{kpi.total_roles}</span>
      </div>
      <div className="mr-kpi-block">
        <span className="label">Avg Cost/1k</span>
        <span className="val">${kpi.avg_role_cost_per_1k.toFixed(4)}</span>
      </div>
    </div>
  );
};

export default KpiPanel;
