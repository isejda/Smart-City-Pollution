<template>
  <select
    class="ds-select"
    :value="modelValue"
    :aria-label="ariaLabel"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
    <option v-for="o in options" :key="o.value" :value="o.value">{{ o.label }}</option>
  </select>
</template>

<script setup>
defineProps({
  options: { type: Array, required: true }, // [{ value, label }]
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  ariaLabel: { type: String, default: '' }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.ds-select {
  width: 100%;
  height: 36px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-card);
  padding: 0 30px 0 11px;
  font-size: 13px;
  font-weight: var(--fw-medium);
  color: var(--text-primary);
  font-family: var(--font-body);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2372767F' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
}
.ds-select:focus-visible { outline: 2px solid var(--teal-400); outline-offset: 1px; }
</style>
