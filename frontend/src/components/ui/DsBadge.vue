<template>
  <span class="ds-badge" :style="style">
    <AppIcon v-if="icon" :icon="icon" :width="12" />
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../AppIcon.vue'

// Prefer explicit fg/bg (the engine's STATUS / SEVERITY / grade objects already
// carry them). `tone` is a convenient fallback for the common semantic colours.
const props = defineProps({
  tone: { type: String, default: 'neutral' },
  fg: { type: String, default: '' },
  bg: { type: String, default: '' },
  icon: { type: String, default: '' }
})

const TONES = {
  neutral: { fg: '#454850', bg: '#F2F2F2' },
  normal: { fg: '#1F8A4C', bg: '#F0FDF4' },
  success: { fg: '#1F8A4C', bg: '#F0FDF4' },
  moderate: { fg: '#C77A00', bg: '#FEF6E7' },
  warning: { fg: '#9A5B00', bg: '#FEF6E7' },
  critical: { fg: '#B1322F', bg: '#F7EDED' },
  danger: { fg: '#B1322F', bg: '#F7EDED' },
  info: { fg: '#4976F4', bg: '#EAF0FE' },
  low: { fg: '#4976F4', bg: '#EAF0FE' }
}

const style = computed(() => {
  const c = props.fg && props.bg ? { fg: props.fg, bg: props.bg } : (TONES[props.tone] || TONES.neutral)
  return { color: c.fg, background: c.bg }
})
</script>

<style scoped>
.ds-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding: 0 8px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-2xs);
  font-weight: var(--fw-bold);
  letter-spacing: .02em;
  white-space: nowrap;
  line-height: 1;
}
</style>
