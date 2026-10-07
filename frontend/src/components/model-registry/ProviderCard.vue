<template>
  <div class="mr-provider-card" :class="{ disabled: !p.enabled }">
    <div class="mr-provider-header">
      <span class="mr-dot" :class="p.connected ? 'ok' : 'err'"></span>
      <span class="mr-name">{{ p.name }}</span>
      <span class="mr-kind" :class="p.kind">{{ p.kind }}</span>
    </div>
    <div class="mr-url">{{ p.base_url || '未配置 base_url' }}</div>
    <div class="mr-meta">
      <span>模型 {{ p.model_count }}</span>
      <span v-if="p.has_key">🔑 已配置</span>
      <span v-else class="mr-warn">⚠️ 无 Key</span>
    </div>
    <div class="mr-actions">
      <button @click="$emit('test', p.id)">测试</button>
      <button @click="$emit('select', p.id)">详情</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProviderCard } from '../../types/model_registry';
defineProps<{ p: ProviderCard }>();
defineEmits<{
  (e: 'test', id: string): void;
  (e: 'select', id: string): void;
}>();
</script>

<style scoped>
.mr-provider-card {
  padding: 12px 14px;
  border-radius: 10px;
  background: #1c1c1e;
  border: 1px solid #2a2a2e;
  color: #e8e8ea;
  font-size: 13px;
  cursor: pointer;
  transition: border-color .15s;
}
.mr-provider-card:hover { border-color: #4a4a52; }
.mr-provider-card.disabled { opacity: .55; }
.mr-provider-header { display: flex; align-items: center; gap: 8px; }
.mr-dot { width: 8px; height: 8px; border-radius: 50%; background: #888; }
.mr-dot.ok { background: #22c55e; box-shadow: 0 0 6px #22c55e88; }
.mr-dot.err { background: #ef4444; }
.mr-name { font-weight: 600; flex: 1; }
.mr-kind {
  font-size: 11px; padding: 1px 6px; border-radius: 6px;
  background: #2e2e34; text-transform: uppercase;
}
.mr-kind.cloud { background: #1e3a8a; color: #c7d2fe; }
.mr-kind.local { background: #14532d; color: #bbf7d0; }
.mr-url { color: #9a9aa0; font-size: 11px; margin: 6px 0; word-break: break-all; }
.mr-meta { display: flex; gap: 10px; color: #b4b4ba; margin-bottom: 8px; }
.mr-warn { color: #f59e0b; }
.mr-actions { display: flex; gap: 6px; }
.mr-actions button {
  flex: 1; padding: 5px 8px; border-radius: 6px; cursor: pointer;
  background: #2a2a2e; color: #e8e8ea; border: 1px solid #33333a;
  font-size: 12px;
}
.mr-actions button:hover { background: #35353b; }
</style>
