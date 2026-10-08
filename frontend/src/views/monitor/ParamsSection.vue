<template>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px">
    <div v-for="p in paramRows" :key="p.key" style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);padding:15px 17px;display:flex;flex-direction:column;gap:10px">
      <div style="display:flex;align-items:center;gap:9px">
        <div style="width:32px;height:32px;border-radius:var(--radius-sm);background:var(--surface-muted);display:flex;align-items:center;justify-content:center">
          <AppIcon :icon="p.icon" :width="17" style="color:var(--text-secondary)" />
        </div>
        <div style="min-width:0;flex:1">
          <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold)">{{ p.label }}</div>
          <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-family:ui-monospace,monospace">{{ p.key }} · {{ p.unit }}</div>
        </div>
        <DsBadge :tone="p.public ? 'neutral' : 'neutral'" :fg="p.public ? 'var(--teal-600)' : ''" :bg="p.public ? 'var(--teal-100)' : ''">{{ p.pubLabel }}</DsBadge>
      </div>
      <div style="height:8px;border-radius:var(--radius-pill)" :style="{ background: p.ramp }"></div>
      <div style="display:flex;justify-content:space-between;font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-semibold)">
        <span>{{ p.lo }}</span><span>{{ p.hi }}</span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px">
        <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:7px 8px">
          <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">NORMAL</div>
          <div style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:var(--green-600);margin-top:2px">{{ p.normal }}</div>
        </div>
        <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:7px 8px">
          <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">KUJDES</div>
          <div style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:#9A5B00;margin-top:2px">{{ p.warn }}</div>
        </div>
        <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:7px 8px">
          <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">KRITIK</div>
          <div style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:var(--danger);margin-top:2px">{{ p.crit }}</div>
        </div>
      </div>
      <div style="font-size:var(--fs-xs);line-height:var(--lh-base);color:var(--text-tertiary)">{{ p.note }}</div>
      <div style="margin-top:auto">
        <DsButton variant="secondary" size="sm" :full-width="true" leading-icon="solar:tuning-2-linear" @click="p.edit()">Konfiguro</DsButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import DsButton from '../../components/ui/DsButton.vue'
import DsBadge from '../../components/ui/DsBadge.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, state } = store

const paramRows = computed(() => {
  state.rev
  return Air.config.params.map(p => ({
    key: p.key, label: p.label, unit: p.unit, icon: p.icon,
    public: p.public,
    pubLabel: p.public ? 'Publik' : 'Vetëm admin',
    ramp: Air.rampCss(p),
    lo: Air.fmtVal(p, p.dispMin) + ' ' + p.unit,
    hi: Air.fmtVal(p, p.dispMax) + ' ' + p.unit,
    normal: p.normal == null ? '-' : Air.fmtVal(p, p.normal),
    warn: p.warn == null ? '-' : Air.fmtVal(p, p.warn),
    crit: p.crit == null ? '-' : Air.fmtVal(p, p.crit),
    note: p.note,
    edit: () => store.openDrawer({ kind: 'param', id: p.key }, { buf: Air.clone(p) })
  }))
})
</script>
