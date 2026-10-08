/* ==========================================================================
   useMonitorStore - shared UI state for the Monitoring Portal.
   --------------------------------------------------------------------------
   A single module-scoped reactive store the shell, sections and drawer all
   read from. It layers portal-only UI state (active section, scope filters,
   the open drawer, toast, list filters) on top of the framework-agnostic
   engine exposed by useAir(). `rev` is bumped whenever engine config is
   mutated in place (settings, drawer saves) so label-only computeds
   recompute even though Air.config is not itself reactive; `snap`/`tick`/
   `lang` cover the replay-driven refreshes.
   ========================================================================== */
import { reactive } from 'vue'
import { useAir } from '../../composables/useAir'

const air = useAir()
const { Air } = air

const state = reactive({
  section: 'overview',
  navOpen: false,
  toast: null,

  // scope bar
  scopeCity: 'all',
  scopeNode: 'all',
  dmode: 'day',

  // shared search + per-section filters
  q: '',
  nodeFilter: 'all',
  mapParam: 'pm25',

  // drawer
  drawer: null,        // { kind:'node'|'param', id }
  dtab: null,
  buf: null,           // editable working copy for node/param forms

  // config-mutation revision (see header)
  rev: 0
})

let toastTimer = null
function toast (msg) {
  if (toastTimer) clearTimeout(toastTimer)
  state.toast = msg
  toastTimer = setTimeout(() => { state.toast = null }, 2600)
}

function bump () { state.rev++ }

/* Re-snapshot at the current clock position (after a settings / source /
   config change), then bump the revision. */
function refreshSnap () {
  air.refresh()
  bump()
}

function go (section) {
  state.section = section
  state.navOpen = false
  state.drawer = null
  state.q = ''
}

function openDrawer (drawer, opts = {}) {
  state.drawer = drawer
  state.dtab = opts.dtab != null ? opts.dtab : null
  state.buf = opts.buf != null ? opts.buf : null
}
function closeDrawer () {
  state.drawer = null
  state.buf = null
}

/* ---- scope helpers (every view states which nodes its numbers refer to) -- */
function scopeNodes () {
  return Air.config.nodes.filter(n =>
    (state.scopeCity === 'all' || n.city === state.scopeCity) &&
    (state.scopeNode === 'all' || n.id === state.scopeNode))
}
function scopeLabel () {
  const ns = scopeNodes()
  if (state.scopeNode !== 'all') {
    const n = Air.nodeById(state.scopeNode)
    return n ? n.name + ' · ' + n.city : '-'
  }
  if (state.scopeCity !== 'all') return ns.length + ' nyje në ' + state.scopeCity
  return 'të gjitha ' + ns.length + ' nyjet e rrjetit'
}
function scopedAvg (snapVal, nodes, key) {
  const vals = nodes.map(n => snapVal.byId[n.id])
    .filter(s => s && s.usable && s.values[key] != null && !s.invalid[key])
    .map(s => s.values[key])
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
}

/* Status → semantic tone map used for DsBadge fallbacks. The engine's
   STATUS/SEVERITY/grade objects carry explicit fg/bg we prefer where present. */
function statusTone (k) {
  return {
    online: 'success', delayed: 'warning', offline: 'danger',
    nodata: 'neutral', inactive: 'neutral', maintenance: 'info'
  }[k] || 'neutral'
}

export function useMonitorStore () {
  return {
    ...air,          // Air, snap, tick, lang, playing, refresh, toggle, seek, t, ...
    state,
    toast,
    bump,
    refreshSnap,
    go,
    openDrawer,
    closeDrawer,
    scopeNodes,
    scopeLabel,
    scopedAvg,
    statusTone
  }
}
