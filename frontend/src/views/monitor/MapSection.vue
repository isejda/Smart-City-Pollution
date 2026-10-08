<template>
  <div style="display:flex;flex-direction:column;gap:12px">
    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:10px 14px">
      <span style="font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary)">SHTRESA</span>
      <span class="adm-tabs">
        <DsTabs variant="pill" :items="mapTabItems" :model-value="state.mapParam" @update:model-value="setMapParam" />
      </span>
      <div style="margin-left:auto;display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <span v-for="s in statusLegend" :key="s.label" style="display:flex;align-items:center;gap:5px;font-size:var(--fs-xs);color:var(--text-secondary);font-weight:var(--fw-medium)">
          <i :style="s.dotStyle"></i>{{ s.label }}
        </span>
      </div>
    </div>
    <div style="position:relative;height:calc(100vh - 210px);min-height:440px;border-radius:var(--radius-md);overflow:hidden;border:1px solid var(--border-subtle);background:#E8EDEA">
      <div ref="mapEl" style="position:absolute;inset:0"></div>
      <div style="position:absolute;left:12px;bottom:12px;z-index:500;background:rgba(255,255,255,.96);border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:9px 12px;box-shadow:var(--shadow-md);width:216px">
        <div style="display:flex;align-items:center;justify-content:space-between;font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide)">
          <span>{{ legend.label }}</span><span style="color:var(--text-tertiary)">{{ legend.unit }}</span>
        </div>
        <div style="height:8px;border-radius:var(--radius-pill);margin-top:6px" :style="{ background: legend.ramp }"></div>
        <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:var(--fs-2xs);font-weight:var(--fw-semibold);color:var(--text-secondary)">
          <span>{{ legend.lo }}</span><span>{{ legend.hi }}</span>
        </div>
        <div style="margin-top:6px;font-size:var(--fs-2xs);color:var(--text-tertiary);line-height:var(--lh-heading)">{{ legend.note }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import L from 'leaflet'
import DsTabs from '../../components/ui/DsTabs.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, snap, tick, scopeNodes } = store
const { state } = store

const mapEl = ref(null)
let map = null
let heat = null
let markers = null

const mapTabItems = computed(() => Air.config.params.map(p => ({ value: p.key, label: p.label, icon: p.icon })))

const statusLegend = computed(() => ['online', 'delayed', 'offline', 'inactive', 'maintenance'].map(k => ({
  label: Air.STATUS[k].label,
  dotStyle: 'width:9px;height:9px;border-radius:50%;display:block;background:' + Air.STATUS[k].dot
})))

const legend = computed(() => {
  state.rev
  const p = Air.paramByKey(state.mapParam)
  return {
    label: p.label.toUpperCase(), unit: p.unit,
    ramp: Air.rampCss(p),
    lo: Air.fmtVal(p, p.dispMin), hi: Air.fmtVal(p, p.dispMax),
    note: p.note
  }
})

function setMapParam (k) { state.mapParam = k; nextTick(syncMap) }

function initMap () {
  if (!mapEl.value || map) return
  map = L.map(mapEl.value, { zoomControl: true, scrollWheelZoom: true, minZoom: 6, maxZoom: 17 }).setView([41.05, 20.2], 8)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap © CARTO', maxZoom: 19, detectRetina: true
  }).addTo(map)
  const p = Air.paramByKey(state.mapParam)
  heat = Air.idwLayer(L, { param: p, radiusM: p.radiusM || 5000, blur: p.blur != null ? p.blur : 0.6, opacity: p.opacity != null ? p.opacity : 0.7 }).addTo(map)
  markers = L.layerGroup().addTo(map)
  fitScope()
  syncMap()
}

function fitScope () {
  if (!map) return
  const fit = scopeNodes()
  if (fit.length) map.fitBounds(L.latLngBounds(fit.map(n => [n.lat, n.lng])), { padding: [50, 50], maxZoom: 15 })
}

function syncMap () {
  const s = snap.value
  if (!map || !s) return
  const p = Air.paramByKey(state.mapParam)
  if (heat) { heat.setOptions({ param: p, radiusM: p.radiusM || 5000, blur: p.blur != null ? p.blur : 0.6, opacity: p.opacity != null ? p.opacity : 0.7 }); heat.setPoints(Air.heatPoints(s, state.mapParam)) }
  markers.clearLayers()
  scopeNodes().forEach(n => {
    const sn = s.byId[n.id]; const st = Air.STATUS[sn.status]
    const v = sn.usable ? sn.values[p.key] : null
    const bad = sn.invalid[p.key]
    const col = (v != null && !bad) ? Air.colorFor(p, v) : '#B8BDC4'
    L.circle([n.lat, n.lng], {
      radius: n.coverageM || 150, color: col, fillColor: col, weight: 1.5,
      opacity: v == null ? 0.3 : 0.75, fillOpacity: v == null ? 0.07 : 0.28, interactive: false
    }).addTo(markers)
    const html = '<div style="position:relative;width:38px;height:38px">' +
      '<div style="width:38px;height:38px;border-radius:var(--radius-full);border:3px solid ' + st.dot + ';background:' + col + ';color:#fff;font:var(--fw-bold) var(--fs-xs)/1 var(--font-display);display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow-md)">' +
      ((v != null && !bad) ? Air.fmtVal(p, v) : '-') + '</div>' +
      '</div>'
    L.marker([n.lat, n.lng], { icon: L.divIcon({ className: '', html, iconSize: [38, 38], iconAnchor: [19, 19] }), title: n.name + ' - ' + st.label })
      .addTo(markers).on('click', () => store.openDrawer({ kind: 'node', id: n.id }, { dtab: 'overview', buf: Air.clone(n) }))
    L.marker([n.lat, n.lng], {
      icon: L.divIcon({ className: '', html: '<div style="font:var(--fw-bold) var(--fs-2xs)/1 var(--font-body);color:var(--text-primary);text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;white-space:nowrap;text-align:center">' + n.id + '</div>', iconSize: [120, 12], iconAnchor: [60, -14] }),
      interactive: false
    }).addTo(markers)
  })
}

onMounted(() => { nextTick(initMap) })
onUnmounted(() => { if (map) { map.remove(); map = null; heat = null; markers = null } })

watch(snap, syncMap)
watch(() => [state.scopeCity, state.scopeNode], () => { syncMap(); fitScope() })
</script>
