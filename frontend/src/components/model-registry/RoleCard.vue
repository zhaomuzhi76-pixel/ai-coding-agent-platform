<template>
  <div class="mr-role-card">
    <div class="mr-role-header">
      <span class="mr-role-label">{{ r.label }}</span>
      <span class="mr-role-key">{{ r.role }}</span>
    </div>
    <div class="mr-role-row">
      <label>主模型</label>
      <select
        :value="local.primary"
        @change="onPrimary(($event.target as HTMLSelectElement).value)"
      >
        <option v-for="c in r.candidates" :key="c.value" :value="c.value">
          [{{ c.group }}] {{ c.label }}
        </option>
      </select>
    </div>
    <div class="mr-role-row">
      <label>降级模型</label>
      <select
        :value="local.fallback || ''"
        @change="onFallback(($event.target as HTMLSelectElement).value)"
      >
        <option value="">— 无 —</option>
        <option v-for="c in r.candidates" :key="c.value" :value="c.value">
          [{{ c.group }}] {{ c.label }}
        </option>
      </select>
    </div>
    <div class="mr-role-status" :class="{ ok: isDirty === false }">
      <span v-if="isDirty">未保存</span>
      <span v-else>✅ 已生效</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, watch } from 'vue';
import type { RoleCard } from '../../types/model_registry';

const props = defineProps<{ r: RoleCard }>();
const emit = defineEmits<{
  (e: 'bind', payload: { role: string; primary: string; fallback: string | null }): void;
}>();

const local = reactive({
  primary: props.r.primary,
  fallback: props.r.fallback,
});

watch(() => props.r, (n) => {
  local.primary = n.primary;
  local.fallback = n.fallback;
}, { deep: true });

const isDirty = computed(
  () => local.primary !== props.r.primary || local.fallback !== props.r.fallback,
);

function onPrimary(v: string) {
  local.primary = v;
  if (isDirty.value) flush();
}
function onFallback(v: string) {
  local.fallback = v || null;
  if (isDirty.value) flush();
}
function flush() {
  emit('bind', {
    role: props.r.role,
    primary: local.primary,
    fallback: local.fallback,
  });
}
</script>

<style scoped>
.mr-role-card {
  padding: 12px 14px; border-radius: 10px;
  background: #1c1c1e; border: 1px solid #2a2a2e;
  color: #e8e8ea; font-size: 13px;
}
.mr-role-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.mr-role-label { font-weight: 600; flex: 1; }
.mr-role-key {
  font-size: 11px; padding: 1px 6px; border-radius: 6px;
  background: #2e2e34; color: #b4b4ba;
}
.mr-role-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
.mr-role-row label { width: 70px; color: #9a9aa0; font-size: 12px; }
.mr-role-row select {
  flex: 1; padding: 5px 8px; border-radius: 6px;
  background: #2a2a2e; color: #e8e8ea; border: 1px solid #33333a;
  font-size: 12px;
}
.mr-role-status { margin-top: 8px; font-size: 11px; color: #f59e0b; }
.mr-role-status.ok { color: #22c55e; }
</style>
