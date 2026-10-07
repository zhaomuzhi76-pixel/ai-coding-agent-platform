# Model Registry Frontend (React)

## Layout
frontend/src/types/model_registry.ts              contract types v1.0.0
frontend/src/composables/useModelRegistry.ts      framework-agnostic API client
frontend/src/styles/model-registry.css            shared styles
frontend/src/components/model-registry/
  ModelRegistryDashboard.tsx                      main container
  ProviderCard.tsx                                provider card
  RoleCard.tsx                                    role routing card
  ModelRegistryDashboard.vue                      Vue3 fallback
  ProviderCard.vue                                Vue3 fallback
  RoleCard.vue                                    Vue3 fallback

## Usage
    import ModelRegistryDashboard from '@/components/model-registry/ModelRegistryDashboard';
    export default function App() { return <ModelRegistryDashboard />; }

## Vite proxy
    server: { proxy: { '/api/model-registry': 'http://localhost:8000' } }
