/** Model Registry 主容器（Dify 风格 + 可拖拽分隔条） */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import ProviderCard from './ProviderCard';
import RoleCard from './RoleCard';
import ProviderDetailModal from './ProviderDetailModal';
import KpiPanel from './KpiPanel';
import CostEstimateCard from './CostEstimateCard';
import { modelRegistryApi } from '../../composables/useModelRegistry';
import type {
  ProviderCard as PC,
  RegistryKPI,
  RoleCard as RC,
} from '../../types/model_registry';
import { ResizeHandle, loadSize } from './_resizable/ResizeHandle';
import '../../styles/model-registry.css';

interface BindPayload {
  role: string;
  primary: string;
  fallback: string | null;
}

const TOP_KEY = 'mr.topHeight';
const SIDE_KEY = 'mr.sideWidth';

export const ModelRegistryDashboard: React.FC = () => {
  const [providers, setProviders] = useState<PC[]>([]);
  const [roles, setRoles] = useState<RC[]>([]);
  const [kpi, setKpi] = useState<RegistryKPI | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [toast, setToast] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PC | null>(null);
  const [topH, setTopH] = useState<number>(() => loadSize(TOP_KEY, 450));
  const [sideW, setSideW] = useState<number>(() => loadSize(SIDE_KEY, 300));
  const toastTimer = useRef<number | null>(null);

  const refresh = useCallback(async () => {
    const [p, r, k] = await Promise.all([
      modelRegistryApi.listProviders(),
      modelRegistryApi.listRoles(),
      modelRegistryApi.getKPI(),
    ]);
    setProviders(p);
    setRoles(r);
    setKpi(k);
  }, []);

  const flash = useCallback((msg: string) => {
    setToast(msg);
    if (toastTimer.current) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(''), 2500);
  }, []);

  const onTest = useCallback(async (id: string) => {
    const res = await modelRegistryApi.testProvider(id);
    flash(`${id} → ${res.connected ? 'OK' : 'FAIL'}`);
    await refresh();
  }, [flash, refresh]);

  const onVerify = useCallback(async (id: string) => {
    try {
      // [VERIFY] 测试并写入已验证，通过的模型会进入 ROLE ROUTING 的✅ 已验证组
      const res = await modelRegistryApi.verifyProvider(id) as {
        verified?: number;
        verified_models?: unknown[];
        models?: unknown[];
      };
      const okCount = res?.verified
        ?? res?.verified_models?.length
        ?? res?.models?.length
        ?? 0;
      flash(`${id} → 已验证 ${okCount} 个模型`);
      await refresh();
    } catch (e) {
      flash(`${id} 验证失败: ${e}`);
    }
  }, [flash, refresh]);

  const onSelect = useCallback((id: string) => {
    setSelectedId(id)
    const p = providers.find((x) => x.id === id) || null;
    setEditing(p);
    setModalOpen(true);
  }, [providers]);

  const onCreate = useCallback(() => {
    setEditing(null);
    setModalOpen(true);
  }, []);

  const onSubmit = useCallback(async (payload: any) => {
    if (editing) {
      await fetch('/api/model-registry/providers/' + editing.id, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } else {
      await modelRegistryApi.createProvider(payload);
    }
    setModalOpen(false);
    flash(editing ? 'updated' : 'created');
    await refresh();
  }, [editing, flash, refresh]);

  const onDelete = useCallback(async (id: string) => {
    await fetch('/api/model-registry/providers/' + id, { method: 'DELETE' });
    setModalOpen(false);
    flash('deleted ' + id);
    await refresh();
  }, [flash, refresh]);

  const onBind = useCallback(async (p: BindPayload) => {
    await modelRegistryApi.bindRole(p);
    flash(`✅ ${p.role} → ${p.primary} 已生效`);
    await refresh();
  }, [flash, refresh]);

  useEffect(() => {
    refresh().catch((e) => flash('load failed: ' + e.message));
    return () => {
      if (toastTimer.current) window.clearTimeout(toastTimer.current);
    };
  }, [refresh, flash]);

  return (
    <div className="mr-dashboard">
      {/* 顶部：KPI + 成本预估（可拖拽调整高度） */}
      <div className="mr-dashboard-top" style={{ ["--mr-top-h" as any]: topH + "px" }}>
        <header className="mr-topbar">
          <h2>Model Registry · LLM Configuration Center</h2>
          {kpi && (
            <div className="mr-kpi">
              <span>Providers <b>{kpi.providers_connected}/{kpi.providers_total}</b></span>
              <span>Models <b>{kpi.models_total}</b></span>
              <span>Roles <b>{kpi.roles_routed}/5</b></span>
            </div>
          )}
        </header>
        <KpiPanel />
        <CostEstimateCard />
      </div>

      {/* 水平分隔条：拖动调整顶部高度 */}
      <ResizeHandle
        direction="horizontal"
        size={topH}
        onResize={setTopH}
        min={260}
        max={900}
        resetValue={450}
        storageKey={TOP_KEY}
      />

      {/* 下方：Providers + Role Routing */}
      <div className="mr-dashboard-body">
        <aside className="mr-side" style={{ width: sideW, flexShrink: 0 }}>
          <h3>Providers</h3>
          <button className="mr-new-btn" onClick={onCreate}>
            + New Provider
          </button>
          {providers.map((p) => (
            <ProviderCard key={p.id} p={p} onTest={onTest} onVerify={onVerify} onSelect={onSelect} />
          ))}
          {selectedId && (
            <p style={{ fontSize: 11, color: '#9a9aa0' }}>
              selected: {selectedId}
            </p>
          )}
        </aside>

        {/* 垂直分隔条：拖动调整左侧宽度 */}
        <ResizeHandle
          direction="vertical"
          size={sideW}
          onResize={setSideW}
          min={200}
          max={600}
          resetValue={300}
          storageKey={SIDE_KEY}
        />

        <main className="mr-main">
          <h3>Role Routing</h3>
          <div className="mr-roles">
            {roles.map((r) => (
              <RoleCard key={r.role} r={r} onBind={onBind} />
            ))}
          </div>
        </main>
      </div>

      {toast && <div className="mr-toast">{toast}</div>}
      <ProviderDetailModal
        open={modalOpen}
        editing={editing}
        onClose={() => setModalOpen(false)}
        onSubmit={onSubmit}
        onDelete={onDelete}
      />
    </div>
  );
};

export default ModelRegistryDashboard;
