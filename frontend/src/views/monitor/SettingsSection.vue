<template>
  <div class="adm-2col" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start">
    <!-- data source -->
    <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:9px">
        <AppIcon icon="solar:database-linear" :width="16" style="color:var(--teal-500)" />
        <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Burimi i të dhënave</h2>
      </div>
      <div style="padding:16px 18px;display:flex;flex-direction:column;gap:14px">
        <button v-for="s in sourceOptions" :key="s.id" :style="s.style" @click="s.go()">
          <span :style="s.radioStyle"></span>
          <span style="flex:1;text-align:left;min-width:0">
            <span style="display:block;font-size:var(--fs-sm);font-weight:var(--fw-semibold)">{{ s.label }}</span>
            <span style="display:block;font-size:var(--fs-xs);color:var(--text-tertiary);margin-top:2px;line-height:var(--lh-heading)">{{ s.detail }}</span>
          </span>
          <DsBadge tone="neutral">{{ s.tag }}</DsBadge>
        </button>
        <div style="display:flex;gap:9px;padding:11px 13px;border-radius:var(--radius-sm);background:var(--amber-100);font-size:var(--fs-xs);line-height:var(--lh-base);color:#7A4A00">
          <AppIcon icon="solar:info-circle-bold" :width="15" style="flex-shrink:0;margin-top:1px" />
          <span>{{ integrationNote }}</span>
        </div>
      </div>
    </section>

    <!-- replay position -->
    <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:9px">
        <AppIcon icon="solar:clock-circle-linear" :width="16" style="color:var(--teal-500)" />
        <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Pozicioni i replay-t</h2>
      </div>
      <div style="padding:16px 18px;display:flex;flex-direction:column;gap:13px">
        <div style="display:flex;align-items:baseline;gap:8px">
          <span style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-h3);letter-spacing:var(--ls-tight)">{{ clockFull }}</span>
          <span style="font-size:var(--fs-xs);color:var(--text-tertiary)">Europe/Tirane</span>
        </div>
        <input type="range" :min="range.from" :max="range.to" :value="cursorVal" aria-label="Pozicioni i replay-t" style="width:100%;accent-color:var(--brand)" @input="setCursor">
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <DsButton v-for="(c, i) in cursorPresets" :key="i" variant="secondary" size="sm" @click="c.go()">{{ c.label }}</DsButton>
        </div>
        <label style="display:flex;flex-direction:column;gap:5px">
          <span style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:var(--text-secondary)">Shpejtësia e replay-t: ×{{ speed }}</span>
          <input type="range" min="1" max="600" :value="speed" aria-label="Shpejtësia e replay-t" style="width:100%;accent-color:var(--brand)" @input="setSpeed">
        </label>
      </div>
    </section>

    <!-- node status rules -->
    <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:9px">
        <AppIcon icon="solar:pulse-2-linear" :width="16" style="color:var(--teal-500)" />
        <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Rregullat e statusit të nyjeve</h2>
      </div>
      <div style="padding:16px 18px;display:flex;flex-direction:column;gap:14px">
        <label v-for="s in statusSettings" :key="s.label" style="display:flex;flex-direction:column;gap:5px">
          <span style="display:flex;align-items:center;justify-content:space-between;font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:var(--text-secondary)">
            <span>{{ s.label }}</span><span style="color:var(--text-primary)">{{ s.value }}</span>
          </span>
          <input type="range" :min="s.min" :max="s.max" :step="s.step" :value="s.raw" :aria-label="s.label" style="width:100%;accent-color:var(--brand)" @input="s.set">
          <span style="font-size:var(--fs-xs);color:var(--text-tertiary);line-height:var(--lh-heading)">{{ s.hint }}</span>
        </label>
      </div>
    </section>

    <!-- persistence + dataset -->
    <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border-subtle);display:flex;align-items:center;gap:9px">
        <AppIcon icon="solar:server-square-linear" :width="16" style="color:var(--teal-500)" />
        <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Persistenca dhe dataset-i</h2>
      </div>
      <div style="padding:16px 18px;display:flex;flex-direction:column;gap:11px">
        <div v-for="d in datasetFacts" :key="d.k" style="display:flex;align-items:baseline;justify-content:space-between;gap:12px;font-size:var(--fs-xs)">
          <span style="color:var(--text-tertiary)">{{ d.k }}</span>
          <span style="font-weight:var(--fw-semibold);text-align:right">{{ d.v }}</span>
        </div>
        <div style="display:flex;gap:9px;padding:11px 13px;border-radius:var(--radius-sm);background:var(--surface-subtle);font-size:var(--fs-xs);line-height:var(--lh-base);color:var(--text-secondary)">
          <AppIcon icon="solar:shield-warning-linear" :width="15" style="flex-shrink:0;margin-top:1px;color:var(--text-tertiary)" />
          <span>{{ persistNote }}</span>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <DsButton variant="secondary" size="sm" leading-icon="solar:restart-linear" @click="resetConfig">Rikthe konfigurimin fillestar</DsButton>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import DsButton from '../../components/ui/DsButton.vue'
import DsBadge from '../../components/ui/DsBadge.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, tick, state } = store

const range = computed(() => Air.source().range())
const cursorVal = computed(() => { tick.value; return Air.clock.t })
const clockFull = computed(() => { tick.value; return Air.fmtDateTime(Air.clock.t) })
const speed = computed(() => { state.rev; return Air.config.settings.replaySpeed })

const integrationNote = 'Adaptori i të dhënave është i izoluar: Air.source() ekspozon readAt(), history(), daily(), diurnal(), meta() dhe packets(). Kalimi te një backend real do të thotë zëvendësim i këtij objekti - asnjë pamje nuk ndryshon.'
const persistNote = 'Konfigurimi i nyjeve dhe parametrave ruhet vetëm në localStorage të këtij shfletuesi. Kjo është një shtresë demonstrimi, jo persistencë prodhimi.'

const sourceOptions = computed(() => {
  state.rev
  const st = Air.config.settings
  return [
    { id: 'dataset', label: 'Dataset (Excel) - replay', detail: Air.DS.source + ' · ' + (Air.DS.rows || 0).toLocaleString('de-DE') + ' matje', tag: 'aktiv' },
    { id: 'rest', label: 'REST API', detail: st.restBase + ' - pikë integrimi, ende e palidhur', tag: 'e palidhur' },
    { id: 'ws', label: 'WebSocket / SSE', detail: st.wsUrl + ' - pikë integrimi, ende e palidhur', tag: 'e palidhur' }
  ].map(s => ({
    ...s,
    style: 'display:flex;align-items:flex-start;gap:11px;padding:12px 13px;border-radius:var(--radius-sm);cursor:pointer;text-align:left;width:100%;font-family:var(--font-body);background:' +
      (st.source === s.id ? 'var(--brand-surface)' : 'var(--surface-card)') + ';border:1px solid ' + (st.source === s.id ? 'var(--teal-200)' : 'var(--border-default)'),
    radioStyle: 'width:16px;height:16px;border-radius:50%;flex-shrink:0;margin-top:2px;border:5px solid ' + (st.source === s.id ? 'var(--brand)' : 'var(--neutral-200)'),
    go: () => {
      if (s.id !== 'dataset') { store.toast('Burimi “' + s.label + '” nuk është i lidhur - kërkohet backend.'); return }
      Air.setSource('dataset'); store.refreshSnap(); store.toast('Burimi u vendos: dataset')
    }
  }))
})

const cursorPresets = computed(() => [
  { label: 'Fillimi i dataset-it', t: range.value.from },
  { label: 'Mbulim maksimal (29 maj)', t: Air.parseTs('2026-05-29 13:00:00') },
  { label: 'Fundi i dataset-it', t: range.value.to }
].map(c => ({ label: c.label, go: () => { Air.clock.pause(); Air.clock.set(c.t); store.toast('Pozicioni u vendos në ' + Air.fmtDateTime(c.t)) } })))

const statusSettings = computed(() => {
  state.rev
  const st = Air.config.settings
  const apply = (key, v) => { st[key] = +v; Air.persist(); store.refreshSnap() }
  return [
    { label: 'Online deri në', value: st.onlineMult + '× intervali', raw: st.onlineMult, min: 1, max: 6, step: 1,
      hint: 'P.sh. për ND-01 me 100 s → online nëse paketa e fundit është më e re se ' + Math.round(100 * st.onlineMult) + ' s.',
      set: e => apply('onlineMult', e.target.value) },
    { label: 'Me vonesë deri në', value: st.delayedMult + '× intervali', raw: st.delayedMult, min: 2, max: 24, step: 1,
      hint: 'Mbi këtë kufi nyja shënohet offline.',
      set: e => apply('delayedMult', e.target.value) },
    { label: 'Dritarja e vlefshmërisë', value: st.validityMin + ' min', raw: st.validityMin, min: 15, max: 720, step: 15,
      hint: 'Matjet më të vjetra nuk publikohen kurrë si gjendje aktuale dhe nuk hyjnë në heatmap.',
      set: e => apply('validityMin', e.target.value) }
  ]
})

const datasetFacts = computed(() => {
  state.rev
  return [
    { k: 'Skedari', v: Air.DS.source },
    { k: 'Rreshta', v: (Air.DS.rows || 0).toLocaleString('de-DE') },
    { k: 'Periudha', v: Air.DS.first + ' → ' + Air.DS.last },
    { k: 'Nyje në dataset', v: Object.keys(Air.DS.nodes).length + ' (3 pajisje testi janë përjashtuar)' },
    { k: 'Zona kohore', v: 'Europe/Tirane (vulat janë kohë lokale)' },
    { k: 'Persistenca', v: Air.store.backend }
  ]
})

function setCursor (e) { Air.clock.pause(); Air.clock.set(+e.target.value) }
function setSpeed (e) { Air.config.settings.replaySpeed = +e.target.value; Air.persist(); store.bump() }
function resetConfig () { Air.store.reset(); store.toast('Konfigurimi u rikthye - rifresko faqen për ta parë') }
</script>
