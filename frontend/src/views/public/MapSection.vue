<template>
  <section class="sec" id="harta" style="padding-bottom:56px">
    <div class="wrap">
      <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;margin-bottom:18px">
        <div>
          <span class="eyebrow" style="color:var(--teal-500)">
            <AppIcon icon="solar:map-point-wave-linear" :width="14" />
            <span>{{ lang === 'en' ? 'LIVE NETWORK' : 'RRJETI LIVE' }}</span>
          </span>
          <h2 style="font-size:29px;margin-top:9px">{{ t('map_title') }}</h2>
          <p class="lede" style="margin-top:8px">{{ t('map_sub') }}</p>
        </div>
        <div class="mapctl" style="display:flex;flex-direction:column;gap:9px;align-items:flex-end">
          <div class="seg" id="cityTabs" role="group">
            <button
              v-for="c in cityTabs"
              :key="c.id"
              :class="{ on: ui.city === c.id }"
              @click="selectCity(c.id)"
            >{{ c.label }}<span style="font-size:10px;opacity:.6;margin-left:5px;font-weight:700">{{ c.count }}</span></button>
          </div>
          <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end" id="paramPills" role="group">
            <button
              v-for="p in paramList"
              :key="p.key"
              class="pill"
              :class="{ on: ui.param === p.key }"
              :title="Air.tp(p, 'long')"
              @click="ui.param = p.key"
            ><i :style="{ background: Air.paramColor(p) }"></i>{{ Air.tp(p, 'label') }}</button>
          </div>
        </div>
      </div>

      <div class="mapbox" id="mapbox">
        <div id="map" ref="mapEl" role="application"></div>

        <div class="ov" id="ovLegend" :class="{ hid: !ui.panels }" style="left:12px;top:12px">
          <div class="ovcard" style="padding:10px 12px;min-width:196px" id="legendCard">
            <div style="display:flex;align-items:center;gap:7px;margin-bottom:7px">
              <AppIcon :icon="p.icon" :width="15" :style="{ color: Air.paramColor(p) }" />
              <b style="font-size:11.5px;font-weight:700">{{ Air.tp(p, 'label') }}</b>
              <span style="font-size:10.5px;color:var(--text-tertiary);margin-left:auto">{{ Air.tp(p, 'unit') }}</span>
            </div>
            <div style="height:8px;border-radius:100px" :style="{ background: Air.rampCss(p) }"></div>
            <div style="display:flex;justify-content:space-between;font-size:9.5px;font-weight:700;color:var(--text-tertiary);margin-top:4px">
              <span>{{ p.dispMin }}</span><span>{{ p.dispMax }}</span>
            </div>
            <div class="lg-status" style="display:flex;gap:12px;margin-top:9px;padding-top:8px;border-top:1px solid var(--border-subtle)">
              <span style="display:flex;align-items:center;gap:5px;font-size:10.5px;font-weight:600;color:var(--text-secondary)"><i style="width:9px;height:9px;border-radius:50%;background:#22A65A;display:block"></i>{{ t('active') }}</span>
              <span style="display:flex;align-items:center;gap:5px;font-size:10.5px;font-weight:600;color:var(--text-secondary)"><i style="width:9px;height:9px;border-radius:50%;background:#B1322F;display:block"></i>{{ t('inactive') }}</span>
            </div>
          </div>
        </div>

        <div class="ov" id="ovCount" :class="{ hid: !ui.panels }" style="left:12px;bottom:12px">
          <div class="ovcard" style="padding:7px 11px;font-size:11.5px;font-weight:600;color:var(--text-secondary)" id="countCard">
            <b style="color:var(--text-primary)">{{ visActiveCount }}</b> / {{ visCount }} {{ t('nodes_shown') }}
          </div>
        </div>

        <div style="position:absolute;right:12px;top:12px;z-index:600;display:flex;flex-direction:column;gap:6px" id="mapTools">
          <button class="btn btn-ghost btn-sm" style="background:#fff;height:34px;width:34px;padding:0" :title="ui.panels ? t('hide_panels') : t('show_panels')" :aria-label="ui.panels ? t('hide_panels') : t('show_panels')" @click="ui.panels = !ui.panels">
            <AppIcon :icon="ui.panels ? 'solar:eye-closed-linear' : 'solar:eye-linear'" :width="17" />
          </button>
          <button class="btn btn-ghost btn-sm" style="background:#fff;height:34px;width:34px;padding:0" :title="t('recenter')" :aria-label="t('recenter')" @click="fitCity(true)">
            <AppIcon icon="solar:gps-linear" :width="17" />
          </button>
          <button v-if="!isSmall" class="btn btn-ghost btn-sm" style="background:#fff;height:34px;width:34px;padding:0" :title="lang === 'en' ? 'Zoom in' : 'Zmadho'" :aria-label="lang === 'en' ? 'Zoom in' : 'Zmadho'" @click="map && map.zoomIn()">
            <AppIcon icon="solar:add-square-linear" :width="17" />
          </button>
          <button v-if="!isSmall" class="btn btn-ghost btn-sm" style="background:#fff;height:34px;width:34px;padding:0" :title="lang === 'en' ? 'Zoom out' : 'Zvogëlo'" :aria-label="lang === 'en' ? 'Zoom out' : 'Zvogëlo'" @click="map && map.zoomOut()">
            <AppIcon icon="solar:minus-square-linear" :width="17" />
          </button>
        </div>

        <NodeDrawer :node-id="ui.node" @close="closeDrawer" />
      </div>

      <div style="display:flex;align-items:center;gap:8px;margin-top:10px;font-size:11.5px;color:var(--text-tertiary);flex-wrap:wrap" id="mapFoot">
        <span style="flex-shrink:0;color:var(--text-tertiary)"><AppIcon icon="solar:info-circle-linear" :width="14" /></span>
        <span>{{ t('coverage_note') }}</span>
        <span class="foot-replay" style="margin-left:auto">{{ t('replay_note') }}</span>
      </div>
    </div>

    <div class="scrim" :class="{ on: ui.node && isMobile }" @click="closeDrawer"></div>
  </section>
</template>

<script setup>
import { computed, ref, inject, onMounted, onUnmounted, watch, nextTick } from 'vue'
import L from 'leaflet'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'
import NodeDrawer from './NodeDrawer.vue'
import { esc } from './chart.js'

const { Air, snap, lang, tick, t } = useAir()
const ui = inject('ui')

const mapEl = ref(null)
let map = null
let markers = {}
let circles = {}

const isMobile = ref(window.innerWidth <= 860)
const isSmall = ref(window.innerWidth <= 560)

function pubNodes() { return Air.config.nodes.filter((n) => n.public) }
function cityNodes(c) { return pubNodes().filter((n) => c === '*' || n.city === c) }
function visNodes() { return cityNodes(ui.city) }
function activeIn(c) { return cityNodes(c).filter((n) => n.active) }
function cities() { return ['Tiranë', 'Korçë', 'Elbasan'] }
function nodeSnap(id) { return snap.value && snap.value.byId[id] }
function isLive(s) { return s && s.node.active && (s.status === 'online' || s.status === 'delayed') }

const p = computed(() => { void lang.value; return Air.paramByKey(ui.param) })

const cityTabs = computed(() => {
  void lang.value
  return [{ id: '*', label: t('all_cities'), count: activeIn('*').length }].concat(
    cities().map((c) => ({ id: c, label: Air.cityName(c), count: activeIn(c).length }))
  )
})
const paramList = computed(() => { void lang.value; return Air.publicParams() })
const visCount = computed(() => { void tick.value; return visNodes().length })
const visActiveCount = computed(() => { void tick.value; return visNodes().filter((n) => n.active).length })

/* ---------------------------------------------------------------- map */
function markerHTML(n, v) {
  var dotCol = n.active ? '#22A65A' : '#B1322F'
  var sel = ui.node === n.id ? ' sel' : ''
  var val = v == null ? '' : '<span class="mkval" style="background:' + Air.colorFor(p.value, v) + '">' + Air.fmtVal(p.value, v) + '</span>'
  return '<div class="mkwrap' + sel + '" style="transform:translate(-50%,-50%)">' +
    '<div class="mkdot" style="background:' + dotCol + '"></div>' + val +
    '<div class="mklbl">' + esc(n.name.split('-')[0].trim()) + '</div></div>'
}

function syncMap() {
  if (!map) return
  var pv = p.value
  var want = {}
  visNodes().forEach((n) => {
    want[n.id] = 1
    var s = nodeSnap(n.id), live = isLive(s)
    var v = live ? s.values[ui.param] : null
    if (v != null && s.invalid[ui.param]) v = null
    var col = v == null ? '#B8BDC4' : Air.colorFor(pv, v)
    var c = circles[n.id]
    if (!c) { c = circles[n.id] = L.circle([n.lat, n.lng], { radius: n.coverageM || 150, weight: 1.5, interactive: false }).addTo(map) }
    c.setLatLng([n.lat, n.lng])
    c.setRadius(n.coverageM || 150)
    c.setStyle({ color: col, fillColor: col, fillOpacity: v == null ? 0.1 : 0.34, opacity: v == null ? 0.35 : 0.75, dashArray: v == null ? '4 4' : null })
    var html = markerHTML(n, v)
    var m = markers[n.id]
    if (!m) {
      m = markers[n.id] = L.marker([n.lat, n.lng], { icon: L.divIcon({ className: '', html: html, iconSize: [0, 0], iconAnchor: [0, 8] }), zIndexOffset: live ? 400 : 200 }).addTo(map)
      m.on('click', () => openNode(n.id))
    } else { m.setLatLng([n.lat, n.lng]); m.setIcon(L.divIcon({ className: '', html: html, iconSize: [0, 0], iconAnchor: [0, 8] })) }
  })
  Object.keys(markers).forEach((id) => {
    if (!want[id]) { map.removeLayer(markers[id]); delete markers[id]; map.removeLayer(circles[id]); delete circles[id] }
  })
}

function fitCity(anim) {
  if (!map) return
  var ns = visNodes().filter((n) => n.active)
  if (!ns.length) ns = visNodes()
  if (!ns.length) return
  var narrow = window.innerWidth <= 860
  var tl = ui.panels ? [narrow ? 26 : 216, narrow ? 116 : 56] : [30, 30]
  var br = [30, ui.panels ? 58 : 30]
  if (ns.length === 1) { map.setView([ns[0].lat, ns[0].lng], 16, { animate: !!anim }); return }
  map.fitBounds(L.latLngBounds(ns.map((n) => [n.lat, n.lng])), { animate: !!anim, paddingTopLeft: tl, paddingBottomRight: br })
}

function openNode(id) {
  ui.node = id
  var n = Air.nodeById(id)
  map.panTo([n.lat, n.lng], { animate: true })
  if (map.getZoom() < 15) map.setZoom(15)
  syncMap()
}
function closeDrawer() { ui.node = null; syncMap() }

function selectCity(c) {
  ui.city = c
  ui.node = null
  nextTick(() => { syncMap(); fitCity(true) })
}

function onResize() {
  isMobile.value = window.innerWidth <= 860
  isSmall.value = window.innerWidth <= 560
  if (map) map.invalidateSize()
}

/* keep the map in sync with replay ticks, param and selection changes */
watch(snap, syncMap)
watch(() => ui.param, syncMap)
watch(() => ui.node, syncMap)

onMounted(() => {
  map = L.map(mapEl.value, { zoomControl: false, scrollWheelZoom: false, minZoom: 6, maxZoom: 18, attributionControl: true })
    .setView([41.3235, 19.8154], 14)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 19, detectRetina: true
  }).addTo(map)
  map.on('click', (e) => {
    if (e.originalEvent && e.originalEvent.target && e.originalEvent.target.closest && e.originalEvent.target.closest('.mkwrap')) return
    closeDrawer()
  })
  syncMap()
  fitCity(false)
  window.addEventListener('resize', onResize)
  setTimeout(() => { if (map) map.invalidateSize() }, 250)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  if (map) { map.remove(); map = null }
  markers = {}; circles = {}
})
</script>
