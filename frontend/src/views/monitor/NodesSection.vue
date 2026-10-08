<template>
  <div style="display:flex;flex-direction:column;gap:14px">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
      <div style="flex:1;min-width:200px;max-width:320px">
        <DsInput :model-value="state.q" placeholder="Kërko nyje, EUI, qytet…" aria-label="Kërko nyje" leading="solar:magnifer-linear" @update:model-value="v => state.q = v" />
      </div>
      <span class="adm-tabs">
        <DsTabs variant="segment" :items="filterItems" :model-value="state.nodeFilter" @update:model-value="v => state.nodeFilter = v" />
      </span>
      <div class="adm-act" style="margin-left:auto">
        <DsButton variant="accent" size="sm" leading-icon="solar:add-circle-linear" @click="newNode">Shto nyje</DsButton>
      </div>
    </div>

    <div style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
      <div class="adm-tbl-wrap">
        <div class="adm-tbl" role="table" aria-label="Nyjet e rrjetit" style="font-size:var(--fs-xs)">
          <div role="row" style="display:grid;grid-template-columns:2.1fr .9fr 1fr 1.1fr .8fr 1fr;gap:8px;padding:10px 16px;background:var(--surface-subtle);font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary)">
            <span role="columnheader">NYJA</span>
            <span role="columnheader">QYTETI</span>
            <span role="columnheader">STATUSI</span>
            <span role="columnheader">PAKETA E FUNDIT</span>
            <span role="columnheader">INTERVALI</span>
            <span role="columnheader">PLOTËSIA</span>
          </div>
          <div
            v-for="n in nodeRows"
            :key="n.id"
            role="row"
            class="adm-tbl-row"
            style="display:grid;grid-template-columns:2.1fr .9fr 1fr 1.1fr .8fr 1fr;gap:8px;align-items:center;padding:11px 16px;border-top:1px solid var(--border-subtle);cursor:pointer"
            @click="n.open()"
          >
            <span role="cell" data-col="NYJA" style="min-width:0">
              <span style="display:block;font-weight:var(--fw-semibold);font-size:var(--fs-sm)">{{ n.name }}</span>
              <span style="display:block;font-size:var(--fs-2xs);color:var(--text-tertiary);font-family:ui-monospace,monospace;margin-top:2px">{{ n.eui }}</span>
            </span>
            <span role="cell" data-col="QYTETI" style="color:var(--text-secondary)">{{ n.city }}</span>
            <span role="cell" data-col="STATUSI">
              <DsBadge :fg="n.statusFg" :bg="n.statusBg">{{ n.statusLabel }}</DsBadge>
            </span>
            <span role="cell" data-col="PAKETA E FUNDIT" style="color:var(--text-secondary)">{{ n.lastSeen }}</span>
            <span role="cell" data-col="INTERVALI" style="color:var(--text-secondary)">{{ n.interval }}</span>
            <span role="cell" data-col="PLOTËSIA" style="display:flex;align-items:center;gap:7px">
              <span style="width:48px;height:5px;border-radius:var(--radius-pill);background:var(--surface-muted);overflow:hidden;display:block"><i :style="n.qualityBar"></i></span>
              <span style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:var(--text-secondary)">{{ n.quality }}</span>
            </span>
          </div>
        </div>
      </div>
      <div v-if="!nodeRows.length" style="padding:34px 18px;text-align:center;font-size:var(--fs-sm);color:var(--text-secondary)">Asnjë nyje nuk përputhet me filtrin.</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import DsInput from '../../components/ui/DsInput.vue'
import DsTabs from '../../components/ui/DsTabs.vue'
import DsButton from '../../components/ui/DsButton.vue'
import DsBadge from '../../components/ui/DsBadge.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, snap, tick, state } = store

const filterItems = [
  { value: 'all', label: 'Të gjitha' },
  { value: 'online', label: 'Online' },
  { value: 'problem', label: 'Me problem' },
  { value: 'inactive', label: 'Jashtë shërbimi' }
]

const nodeRows = computed(() => {
  const s = snap.value; tick.value; state.rev
  if (!s) return []
  const q = state.q.toLowerCase()
  return Air.config.nodes.filter(n => {
    const sn = s.byId[n.id]
    if (state.nodeFilter === 'online' && sn.status !== 'online') return false
    if (state.nodeFilter === 'problem' && ['online', 'inactive'].indexOf(sn.status) >= 0 && !Object.keys(sn.invalid).length) return false
    if (state.nodeFilter === 'inactive' && n.active) return false
    if (!q) return true
    return (n.name + ' ' + n.eui + ' ' + n.city + ' ' + n.id).toLowerCase().indexOf(q) >= 0
  }).map(n => {
    const sn = s.byId[n.id]; const st = Air.STATUS[sn.status]
    return {
      id: n.id, name: n.name, eui: n.eui, city: n.city,
      statusLabel: st.label, statusFg: st.fg, statusBg: st.bg,
      lastSeen: sn.packetAt ? Air.fmtAge(sn.ageMs) + ' më parë' : 'asnjëherë',
      interval: n.intervalS >= 60 ? Math.round(n.intervalS / 6) / 10 + ' min' : n.intervalS + ' s',
      quality: Math.round(sn.quality * 100) + '%',
      qualityBar: 'display:block;height:100%;border-radius:var(--radius-pill);width:' + Math.round(sn.quality * 100) + '%;background:' +
        (sn.quality > 0.75 ? 'var(--green-500)' : sn.quality > 0.4 ? 'var(--amber-500)' : 'var(--danger)'),
      open: () => store.openDrawer({ kind: 'node', id: n.id }, { dtab: 'overview', buf: Air.clone(n) })
    }
  })
})

function newNode () {
  const id = Air.nextNodeId()
  store.openDrawer({ kind: 'node', id }, {
    dtab: 'config',
    buf: {
      id, eui: '', joinEui: '', name: 'Nyje e re', city: 'Tiranë', place: '', address: '', lat: 41.32, lng: 19.82,
      transport: 'LoRaWAN', hw: '', installedAt: '2026-06-30', intervalS: 300, active: true, public: false, maintenance: false,
      scale: { snd: 1023, uv: 1023, rain: 1023 }, sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv'], apiId: '', tz: 'Europe/Tirane', notes: '',
      tech: 'lorawan', coverageM: 150, webhook: 'https://api.smartcitypollution.al/v1/ingest/' + id.toLowerCase(), params: {}
    }
  })
}
</script>

<style scoped>
.adm-tbl-row:hover { background: var(--surface-subtle); }
</style>
