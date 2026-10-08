<template>
  <button
    class="ds-switch"
    :class="{ on: modelValue }"
    role="switch"
    :aria-checked="String(modelValue)"
    :aria-label="ariaLabel"
    @click="$emit('update:modelValue', !modelValue)"
  >
    <span class="ds-switch-knob"></span>
  </button>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  ariaLabel: { type: String, default: '' }
})
defineEmits(['update:modelValue'])
</script>

<style scoped>
.ds-switch {
  width: 40px;
  height: 22px;
  border-radius: var(--radius-pill);
  border: none;
  background: var(--neutral-200);
  position: relative;
  cursor: pointer;
  padding: 0;
  transition: background 160ms var(--ease-standard);
  flex-shrink: 0;
}
.ds-switch.on { background: var(--brand); }
.ds-switch-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow-xs);
  transition: transform 160ms var(--ease-standard);
}
.ds-switch.on .ds-switch-knob { transform: translateX(18px); }
</style>
