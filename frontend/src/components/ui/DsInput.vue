<template>
  <div class="ds-input" :class="{ 'ds-input--icon': leading }">
    <AppIcon v-if="leading" :icon="leading" :width="15" class="ds-input-lead" />
    <input
      :value="modelValue"
      :placeholder="placeholder"
      :aria-label="ariaLabel || placeholder"
      :type="type"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script setup>
import AppIcon from '../AppIcon.vue'

defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  ariaLabel: { type: String, default: '' },
  leading: { type: String, default: '' },
  type: { type: String, default: 'text' }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.ds-input { position: relative; display: flex; align-items: center; width: 100%; }
.ds-input-lead { position: absolute; left: 11px; color: var(--text-tertiary); pointer-events: none; }
.ds-input input {
  width: 100%;
  height: 36px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-card);
  padding: 0 12px;
  font-size: 13px;
  font-family: var(--font-body);
  color: var(--text-primary);
}
.ds-input--icon input { padding-left: 34px; }
.ds-input input::placeholder { color: var(--text-tertiary); }
.ds-input input:focus-visible { outline: 2px solid var(--teal-400); outline-offset: 1px; }
</style>
