<template>
  <header style="position:sticky;top:0;z-index:900;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);border-bottom:1px solid var(--border-subtle)">
    <div style="display:flex;align-items:center;gap:12px;padding:12px 22px;flex-wrap:wrap">
      <div id="adm-burger" style="display:none">
        <DsIconButton variant="surface" aria-label="Hap menunë" @click="state.navOpen = true">
          <AppIcon icon="solar:hamburger-menu-linear" :width="18" />
        </DsIconButton>
      </div>
      <div style="min-width:0">
        <h1 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-h3);letter-spacing:var(--ls-tight);margin:0">{{ pageTitle }}</h1>
        <div class="adm-sub" style="font-size:var(--fs-xs);color:var(--text-tertiary);margin-top:2px">{{ pageSub }}</div>
      </div>

      <div style="margin-left:auto;display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:9px;height:32px;padding:0 12px;border-radius:var(--radius-sm);border:1px solid var(--border-default);background:var(--surface-card)">
          <span :style="liveDotStyle"></span>
          <span style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);white-space:nowrap">{{ clockLabel }}</span>
          <span class="adm-hide-sm" style="font-size:var(--fs-xs);color:var(--text-tertiary)">{{ clockMode }}</span>
        </div>
        <DsIconButton variant="surface" aria-label="Nis ose ndalo replay-n" @click="toggle">
          <AppIcon :icon="playing ? 'solar:pause-bold' : 'solar:play-bold'" :width="16" />
        </DsIconButton>
        <span class="adm-hide-xs">
          <DsButton variant="secondary" size="sm" leading-icon="solar:refresh-linear" @click="onRefresh">Rifresko</DsButton>
        </span>
        <DsIconButton variant="surface" aria-label="Dil" @click="logout">
          <AppIcon icon="solar:logout-2-linear" :width="16" />
        </DsIconButton>
      </div>
    </div>

    <div class="adm-scope" style="display:flex;align-items:center;gap:9px;padding:9px 22px;border-top:1px solid var(--border-subtle);background:var(--surface-subtle);flex-wrap:wrap">
      <AppIcon class="adm-scope-lbl" icon="solar:filter-linear" :width="14" style="color:var(--text-tertiary);flex-shrink:0" />
      <span class="adm-scope-lbl" style="font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary);white-space:nowrap">TË DHËNAT I REFEROHEN</span>
      <div class="adm-scope-sel" style="width:158px">
        <DsSelect :model-value="state.scopeCity" :options="scopeCityOptions" aria-label="Qyteti" @update:model-value="setScopeCity" />
      </div>
      <div class="adm-scope-sel" style="width:250px">
        <DsSelect :model-value="state.scopeNode" :options="scopeNodeOptions" aria-label="Nyja" @update:model-value="setScopeNode" />
      </div>
      <span class="adm-scope-txt" style="font-size:var(--fs-xs);color:var(--text-secondary);font-weight:var(--fw-medium)">{{ scopeText }}</span>
      <DsButton v-if="scopeDirty" variant="ghost" size="sm" @click="clearScope">Hiq filtrin</DsButton>
      <div class="adm-scope-modes" style="margin-left:auto">
        <span class="adm-tabs">
          <DsTabs variant="segment" :items="dmodeItems" :model-value="state.dmode" @update:model-value="v => state.dmode = v" />
        </span>
      </div>
    </div>

    <div v-if="state.toast" style="display:flex;align-items:center;gap:9px;padding:9px 22px;background:var(--brand-surface);border-top:1px solid var(--teal-200);font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:var(--teal-600)">
      <AppIcon icon="solar:check-circle-bold" :width="15" />{{ state.toast }}
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import DsButton from '../../components/ui/DsButton.vue'
import DsIconButton from '../../components/ui/DsIconButton.vue'
import DsSelect from '../../components/ui/DsSelect.vue'
import DsTabs from '../../components/ui/DsTabs.vue'
import { useMonitorStore } from './useMonitorStore'
import { useAuthStore } from '@/stores/auth'

const store = useMonitorStore()
const { Air, state, tick, playing, toggle, scopeLabel } = store
const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/')
}

const TITLES = {
  overview: () => ['Përmbledhje operative', 'Gjendja e rrjetit në ' + Air.fmtDateTime(Air.clock.t) + ' (Europe/Tirane)'],
  map: () => ['Harta operative', 'Statuset e nyjeve mbi shtresën e zgjedhur të parametrit'],
  nodes: () => ['Nyjet', Air.config.nodes.length + ' nyje të konfiguruara · ' + Air.config.nodes.filter(n => n.active).length + ' aktive'],
  params: () => ['Parametrat', 'Pragjet, shkallët e ngjyrave dhe kalibrimi që përdor portali publik'],
  reports: () => ['Raportet', 'Vëllimi i të dhënave, mbulimi i parametrave dhe njoftimet e dërguara'],
  settings: () => ['Burimi & cilësimet', 'Adaptori i të dhënave, replay-i dhe rregullat e statusit']
}

const title = computed(() => { tick.value; state.rev; return (TITLES[state.section] || TITLES.overview)() })
const pageTitle = computed(() => title.value[0])
const pageSub = computed(() => title.value[1])

const clockLabel = computed(() => { tick.value; return Air.fmtDateTime(Air.clock.t) })
const clockMode = computed(() => { tick.value; return playing.value ? '×' + Air.config.settings.replaySpeed : 'pauzë' })
const liveDotStyle = computed(() => {
  tick.value
  return 'width:7px;height:7px;border-radius:50%;display:block;background:' +
    (playing.value ? 'var(--green-500);animation:admpulse 2.4s ease-in-out infinite' : 'var(--amber-500)')
})

const scopeCityOptions = computed(() => {
  state.rev
  return [{ value: 'all', label: 'Të gjitha qytetet' }]
    .concat(Air.cities().map(c => ({ value: c, label: c + ' (' + Air.config.nodes.filter(n => n.city === c).length + ')' })))
})
const scopeNodeOptions = computed(() => {
  state.rev
  return [{ value: 'all', label: 'Të gjitha nyjet' }]
    .concat(Air.config.nodes.filter(n => state.scopeCity === 'all' || n.city === state.scopeCity)
      .map(n => ({ value: n.id, label: n.id + ' - ' + n.name })))
})
const scopeText = computed(() => { tick.value; state.rev; return scopeLabel() })
const scopeDirty = computed(() => state.scopeCity !== 'all' || state.scopeNode !== 'all')

const dmodeItems = [
  { value: 'day', label: 'Dita' },
  { value: 'week', label: 'Java' },
  { value: 'month', label: 'Muaji' }
]

function setScopeCity (v) { state.scopeCity = v; state.scopeNode = 'all' }
function setScopeNode (v) { state.scopeNode = v }
function clearScope () { state.scopeCity = 'all'; state.scopeNode = 'all' }
function onRefresh () { store.refreshSnap(); store.toast('Të dhënat u rifreskuan nga ' + Air.source().label) }
</script>
