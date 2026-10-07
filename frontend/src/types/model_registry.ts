// 自动契约类型 - 来源: contracts/model_registry.v1.json (v1.0.0)
// 手动修改将被契约冻结覆盖，如需变更请改 backend/core/model_registry/contract.py

// Provider 具体类型（ollama/openai/anthropic/dashscope/... ）
export type ProviderKind = string;

export interface ProviderKindSpec {
  value: string;
  label: string;
  category: 'local' | 'cloud';
  default_base_url: string;
  needs_key: boolean;
  protocol: string;
}

export interface ProviderCard {
  id: string;
  name: string;
  kind: ProviderKind;
  base_url: string;
  has_key: boolean;
  enabled: boolean;
  connected: boolean;
  model_count: number;
}

export interface ModelCard {
  id: string;
  display: string;
  provider: string;
  ctx: number;
  cost_per_1k: number;
  tags: string[];
}

export interface RoleCandidate {
  value: string;
  label: string;
  group: string;
}

export interface RoleCard {
  role: string;
  label: string;
  primary: string;
  primary_provider: string;
  fallback: string | null;
  ui: 'select';
  candidates: RoleCandidate[];
}

export interface VerifiedModel {
  id: string;
  provider: string;
  display_name: string;
  label: string;
}

export interface RegistryKPI {
  providers_total: number;
  providers_connected: number;
  models_total: number;
  roles_routed: number;
}

export interface CreateProviderPayload {
  id: string;
  name?: string;
  kind: ProviderKind;
  base_url: string;
  api_key?: string;
  enabled?: boolean;
}

export interface BindRolePayload {
  role: string;
  primary: string;
  fallback?: string | null;
}

export interface SimpleOK { ok: boolean; }
export interface CreateProviderResult extends SimpleOK { id: string; }
export interface TestProviderResult { provider: string; connected: boolean; }

export const API_PATHS = {
  listProviders:  '/api/model-registry/providers',
  createProvider: '/api/model-registry/providers',
  listModels:     (id: string) => `/api/model-registry/providers/${id}/models`,
  testProvider:   (id: string) => `/api/model-registry/providers/${id}/test`,
  listRoles:      '/api/model-registry/roles',
  bindRole:       '/api/model-registry/roles',
  getKPI:         '/api/model-registry/kpi',
  verifyProvider: (id: string) => `/api/model-registry/providers/${id}/verify`,
  verifiedModels: '/api/model-registry/verified-models',
  providerKinds: '/api/model-registry/provider-kinds',
} as const;

export interface ModelRegistryClient {
  listProviders(): Promise<ProviderCard[]>;
  listModels(providerId: string): Promise<ModelCard[]>;
  listRoles(): Promise<RoleCard[]>;
  getKPI(): Promise<RegistryKPI>;
  createProvider(p: CreateProviderPayload): Promise<CreateProviderResult>;
  bindRole(p: BindRolePayload): Promise<SimpleOK>;
  testProvider(id: string): Promise<TestProviderResult>;
}
