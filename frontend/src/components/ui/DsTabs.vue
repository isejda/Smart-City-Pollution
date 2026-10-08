<template>
  <div class="ds-tabs" :class="`ds-tabs--${variant}`" role="group">
    <button
      v-for="it in items"
      :key="it.value"
      class="ds-tab"
      :class="{ on: it.value === modelValue }"
      @click="$emit('update:modelValue', it.value)"
    >
      <i v-if="it.dot" class="ds-tab-dot" :style="{ background: it.dot }"></i>
      <AppIcon v-if="it.icon" :icon="it.icon" :width="14" />
      {{ it.label }}
    </button>
  </div>
</template>

<script setup>
import AppIcon from '../AppIcon.vue'

defineProps({
  items: { type: Array, required: true },   // [{ value, label, dot?, icon? }]
  modelValue: { type: [String, Number], default: '' },
  variant: { type: String, default: 'segment' } // segment | pill
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
/* segment (a single grouped control) */
.ds-tabs--segment {
  display: inline-flex;
  background: var(--surface-muted);
  border: 1px solid var(--border-subtle);
  border-radius: 9px;
  padding: 3px;
  gap: 2px;
}
.ds-tabs--segment .ds-tab {
  border: none;
  background: transparent;
  height: 30px;
  padding: 0 13px;
  border-radius: 7px;
  font-size: 12.5px;
  font-weight: var(--fw-semibold);
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all 140ms;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.ds-tabs--segment .ds-tab:hover { color: var(--text-primary); }
.ds-tabs--segment .ds-tab.on {
  background: var(--surface-card);
  color: var(--teal-500);
  box-shadow: var(--shadow-xs);
}

/* pill (separate rounded chips) */
.ds-tabs--pill { display: inline-flex; gap: 6px; flex-wrap: wrap; }
.ds-tabs--pill .ds-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-default);
  background: var(--surface-card);
  font-size: 12.5px;
  font-weight: var(--fw-semibold);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 140ms;
}
.ds-tabs--pill .ds-tab:hover { border-color: var(--teal-400); color: var(--teal-500); }
.ds-tabs--pill .ds-tab.on { background: var(--teal-500); border-color: var(--teal-500); color: #fff; }

.ds-tab-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
</style>
