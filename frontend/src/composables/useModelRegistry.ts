// 框架无关的 model_registry API 客户端（Vue3/React 均可复用）
// 契约来源: contracts/model_registry.v1.json (v1.0.0)
import type {
  ProviderCard, ModelCard, RoleCard, RegistryKPI,
  CreateProviderPayload, BindRolePayload, SimpleOK,
  CreateProviderResult, TestProviderResult,
} from '../types/model_registry';
import { API_PATHS } from '../types/model_registry';

const BASE = '';

async function _fetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`[${res.status}] ${path}: ${text || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const modelRegistryApi = {
  listProviders: () =>
    _fetch<ProviderCard[]>(API_PATHS.listProviders),
  listModels: (id: string) =>
    _fetch<ModelCard[]>(API_PATHS.listModels(id)),
  listRoles: () =>
    _fetch<RoleCard[]>(API_PATHS.listRoles),
  getKPI: () =>
    _fetch<RegistryKPI>(API_PATHS.getKPI),
  createProvider: (p: CreateProviderPayload) =>
    _fetch<CreateProviderResult>(API_PATHS.createProvider, {
      method: 'POST', body: JSON.stringify(p),
    }),
  bindRole: (p: BindRolePayload) =>
    _fetch<SimpleOK>(API_PATHS.bindRole, {
      method: 'POST', body: JSON.stringify(p),
    }),
  testProvider: (id: string) =>
    _fetch<TestProviderResult>(API_PATHS.testProvider(id), {
      method: 'POST',
    }),
  verifyProvider: (id: string) =>
    _fetch<Record<string, unknown>>(API_PATHS.verifyProvider(id), {
      method: 'POST',
    }),
};
