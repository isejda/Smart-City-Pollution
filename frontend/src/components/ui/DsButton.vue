<template>
  <button
    class="ds-btn"
    :class="[`ds-btn--${variant}`, `ds-btn--${size}`, { 'ds-btn--full': fullWidth }]"
    :type="type"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <AppIcon v-if="leadingIcon" :icon="leadingIcon" :width="size === 'sm' ? 15 : 16" />
    <span v-if="$slots.default"><slot /></span>
    <AppIcon v-if="trailingIcon" :icon="trailingIcon" :width="size === 'sm' ? 15 : 16" />
  </button>
</template>

<script setup>
import AppIcon from '../AppIcon.vue'

defineProps({
  variant: { type: String, default: 'secondary' }, // primary | secondary | accent | ghost
  size: { type: String, default: 'md' },            // sm | md
  type: { type: String, default: 'button' },
  leadingIcon: { type: String, default: '' },
  trailingIcon: { type: String, default: '' },
  fullWidth: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false }
})
defineEmits(['click'])
</script>

<style scoped>
.ds-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 38px;
  padding: 0 15px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: var(--fw-semibold);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 160ms var(--ease-standard);
  white-space: nowrap;
  font-family: var(--font-body);
}
.ds-btn:disabled { opacity: .5; cursor: not-allowed; }
.ds-btn--full { width: 100%; }

.ds-btn--sm { height: 32px; padding: 0 12px; font-size: 12px; border-radius: 7px; }

.ds-btn--secondary { border-color: var(--border-default); background: var(--surface-card); color: var(--text-secondary); }
.ds-btn--secondary:hover:not(:disabled) { border-color: var(--teal-400); color: var(--teal-500); }

.ds-btn--accent { background: var(--brand); color: var(--brand-on); }
.ds-btn--accent:hover:not(:disabled) { background: var(--brand-hover); }

.ds-btn--primary { background: var(--action-primary); color: var(--action-on-primary); }
.ds-btn--primary:hover:not(:disabled) { background: var(--action-primary-hover); }

.ds-btn--ghost { background: transparent; color: var(--text-secondary); }
.ds-btn--ghost:hover:not(:disabled) { background: var(--surface-muted); color: var(--text-primary); }
</style>
