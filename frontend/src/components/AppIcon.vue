<template>
  <Icon :icon="icon" :width="sz" :height="sz" :style="{ display: 'inline-flex', flexShrink: 0 }" aria-hidden="true" />
</template>

<script setup>
// Thin wrapper over @iconify/vue so the whole app references icons the same
// way the original design did (solar:* / mdi:* names, sized in px).
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps({
  icon: { type: String, required: true },
  width: { type: [Number, String], default: 16 }
})

const sz = computed(() => Number(props.width))
</script>
