<template>
  <button
    class="ds-iconbtn"
    :class="`ds-iconbtn--${variant}`"
    :aria-label="ariaLabel"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'surface' }, // surface | ghost
  ariaLabel: { type: String, default: '' }
})
defineEmits(['click'])
</script>

<style scoped>
.ds-iconbtn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 150ms var(--ease-standard);
  color: var(--text-secondary);
}
.ds-iconbtn--surface { border: 1px solid var(--border-default); background: var(--surface-card); }
.ds-iconbtn--surface:hover { border-color: var(--teal-400); color: var(--teal-500); }
.ds-iconbtn--ghost { border: none; background: transparent; }
.ds-iconbtn--ghost:hover { background: var(--surface-muted); color: var(--text-primary); }
</style>
