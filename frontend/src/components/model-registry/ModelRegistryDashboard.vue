<template>
  <div class="mr-dashboard">
    <header class="mr-topbar">
      <h2>⚙️ Model Registry · 大模型配置中心</h2>
      <div class="mr-kpi" v-if="kpi">
        <span>Providers <b>{{ kpi.providers_connected }}/{{ kpi.providers_total }}</b></span>
        <span>Models <b>{{ kpi.models_total }}</b></span>
        <span>Roles <b>{{ kpi.roles_routed }}/5</b></span>
      </div>
    </header>

    <div class="mr-body">
      <aside class="mr-side">
        <h3>Providers</h3>
        <ProviderCard
          v-for="p in providers" :key="p.id" :p="p"
          @test="onTest" @select="selectedId = p.id"
        />
      </aside>

      <main class="mr-main">
        <h3>角色路由（5 张卡片）</h3>
        <div class="mr-roles">
          <RoleCard
            v-for="r in roles" :key="r.role" :r="r"
            @bind="onBind"
          />
        </div>
        <p v-if="toast" class="mr-toast">{{ toast }}</p>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import ProviderCard from './ProviderCard.vue';
import RoleCard from './RoleCard.vue';
import { modelRegistryApi } from '../../composables/useModelRegistry';
import type {
  ProviderCard as PC, RoleCard as RC, RegistryKPI,
} from '../../types/model_registry';

const providers = ref<PC[]>([]);
const roles = ref<RC[]>([]);
const kpi = ref<RegistryKPI | null>(null);
const selectedId = ref<string | null>(null);
const toast = ref('');

async function refresh() {
  const [p, r, k] = await Promise.all([
    modelRegistryApi.listProviders(),
    modelRegistryApi.listRoles(),
    modelRegistryApi.getKPI(),
  ]);
  providers.value = p;
  roles.value = r;
  kpi.value = k;
}

async function onTest(id: string) {
  const res = await modelRegistryApi.testProvider(id);
  toast.value = `${id} → ${res.connected ? '✅ 连通' : '❌ 失败'}`;
  await refresh();
  setTimeout(() => (toast.value = ''), 2000);
}

async function onBind(p: { role: string; primary: string; fallback: string | null }) {
  await modelRegistryApi.bindRole(p);
  toast.value = `${p.role} 已切换到 ${p.primary}`;
  await refresh();
  setTimeout(() => (toast.value = ''), 2000);
}

onMounted(refresh);
</script>

<style scoped>
.mr-dashboard { display: flex; flex-direction: column; height: 100%; background: #131316; color: #e8e8ea; }
.mr-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 20px; border-bottom: 1px solid #26262b;
}
.mr-topbar h2 { font-size: 15px; margin: 0; font-weight: 600; }
.mr-kpi { display: flex; gap: 18px; font-size: 12px; color: #b4b4ba; }
.mr-kpi b { color: #e8e8ea; }
.mr-body { display: flex; flex: 1; overflow: hidden; }
.mr-side {
  width: 280px; padding: 14px; overflow-y: auto;
  border-right: 1px solid #26262b; display: flex; flex-direction: column; gap: 10px;
}
.mr-side h3, .mr-main h3 { font-size: 12px; color: #9a9aa0; margin: 0 0 8px; text-transform: uppercase; letter-spacing: .5px; }
.mr-main { flex: 1; padding: 14px; overflow-y: auto; }
.mr-roles { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 12px; }
.mr-toast {
  position: fixed; bottom: 20px; right: 20px;
  padding: 8px 14px; border-radius: 8px; background: #2a2a2e;
  color: #e8e8ea; font-size: 12px; border: 1px solid #33333a;
}
</style>
