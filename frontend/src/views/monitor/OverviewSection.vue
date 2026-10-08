<template>
  <div style="display:flex;flex-direction:column;gap:16px">
    <!-- KPI cards -->
    <div class="adm-kpi" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
      <div v-for="(k, i) in kpis" :key="i" style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:14px 16px;box-shadow:var(--shadow-xs)">
        <div style="display:flex;align-items:flex-start;gap:7px;font-size:var(--fs-xs);font-weight:var(--fw-medium);line-height:var(--lh-heading);color:var(--text-tertiary);min-height:32px">
          <AppIcon :icon="k.icon" :width="14" :style="{ flexShrink: 0, marginTop: '2px', color: k.color || 'var(--text-tertiary)' }" />{{ k.label }}
        </div>
        <div style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-h2);letter-spacing:var(--ls-tight);margin-top:6px" :style="k.color ? { color: k.color } : {}">{{ k.value }}</div>
        <div style="font-size:var(--fs-xs);color:var(--text-tertiary);margin-top:2px">{{ k.sub }}</div>
      </div>
    </div>

    <div class="adm-2col" style="display:grid;grid-template-columns:1.45fr 1fr;gap:16px">
      <!-- city environmental table -->
      <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
        <div style="display:flex;align-items:center;gap:9px;padding:14px 18px;border-bottom:1px solid var(--border-subtle)">
          <AppIcon icon="solar:city-linear" :width="16" style="color:var(--teal-500)" />
          <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Gjendja mjedisore sipas qyteteve</h2>
        </div>
        <div class="adm-tbl-wrap">
          <div class="adm-tbl" role="table" aria-label="Gjendja mjedisore sipas qyteteve" style="font-size:var(--fs-xs)">
            <div role="row" style="display:grid;grid-template-columns:1.5fr .9fr .8fr .8fr .8fr 1.1fr;gap:8px;padding:9px 18px;background:var(--surface-subtle);font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary)">
              <span role="columnheader">QYTETI</span>
              <span role="columnheader">NYJE</span>
              <span role="columnheader" style="text-align:right">PM2.5</span>
              <span role="columnheader" style="text-align:right">PM10</span>
              <span role="columnheader" style="text-align:right">TEMP.</span>
              <span role="columnheader" style="text-align:right">GJENDJA</span>
            </div>
            <div v-for="ct in cityRows" :key="ct.name" role="row" style="display:grid;grid-template-columns:1.5fr .9fr .8fr .8fr .8fr 1.1fr;gap:8px;align-items:center;padding:11px 18px;border-top:1px solid var(--border-subtle)">
              <span role="cell" data-col="QYTETI" style="font-weight:var(--fw-semibold);font-size:var(--fs-sm)">{{ ct.name }}</span>
              <span role="cell" data-col="NYJE" style="color:var(--text-secondary)">{{ ct.nodes }}</span>
              <span role="cell" data-col="PM2.5" style="text-align:right;font-weight:var(--fw-semibold)" :style="{ color: ct.pm25Col }">{{ ct.pm25 }}</span>
              <span role="cell" data-col="PM10" style="text-align:right;font-weight:var(--fw-semibold)" :style="{ color: ct.pm10Col }">{{ ct.pm10 }}</span>
              <span role="cell" data-col="TEMP." style="text-align:right;font-weight:var(--fw-semibold)" :style="{ color: ct.tmpCol }">{{ ct.tmp }}</span>
              <span role="cell" data-col="GJENDJA" style="text-align:right">
                <DsBadge :tone="ct.gradeTone" :fg="ct.gradeFg" :bg="ct.gradeBg">{{ ct.grade }}</DsBadge>
              </span>
            </div>
          </div>
        </div>
        <div style="padding:12px 18px;border-top:1px solid var(--border-subtle);background:var(--surface-subtle);font-size:var(--fs-xs);color:var(--text-tertiary);line-height:var(--lh-base)">{{ cityNote }}</div>
      </section>

      <!-- latest by parameter -->
      <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
        <div style="display:flex;align-items:center;gap:9px;padding:14px 18px;border-bottom:1px solid var(--border-subtle)">
          <AppIcon icon="solar:pulse-linear" :width="16" style="color:var(--teal-500)" />
          <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Matjet e fundit sipas parametrit</h2>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border-subtle)">
          <div v-for="p in paramTiles" :key="p.label" style="background:var(--surface-card);padding:13px 15px">
            <div style="display:flex;align-items:center;gap:6px;font-size:var(--fs-xs);color:var(--text-tertiary);font-weight:var(--fw-medium)">
              <AppIcon :icon="p.icon" :width="13" />{{ p.label }}
            </div>
            <div style="display:flex;align-items:baseline;gap:4px;margin-top:5px">
              <span style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-h3);letter-spacing:var(--ls-tight)" :style="{ color: p.color }">{{ p.value }}</span>
              <span style="font-size:var(--fs-2xs);color:var(--text-tertiary)">{{ p.unit }}</span>
            </div>
            <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:3px">{{ p.sub }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import DsBadge from '../../components/ui/DsBadge.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, snap, tick, scopeNodes, scopedAvg } = store

const GRADE_TONE = { critical: 'danger', warning: 'warning', moderate: 'moderate', low: 'low', normal: 'normal' }

const kpis = computed(() => {
  const s = snap.value; tick.value
  if (!s) return []
  const ns = scopeNodes()
  const by = k => ns.filter(n => s.byId[n.id].status === k).length
  const invalid = ns.filter(n => Object.keys(s.byId[n.id].invalid).length > 0).length
  const usable = ns.filter(n => s.byId[n.id].usable)
  const completeness = usable.length ? Math.round(usable.reduce((t, n) => t + s.byId[n.id].quality, 0) / usable.length * 100) : 0
  const upt = ns.filter(n => n.active).length
  const availability = upt ? Math.round(ns.filter(n => n.active && s.byId[n.id].status === 'online').length / upt * 100) : 0
  const st = Air.config.settings
  return [
    { label: 'Nyje të konfiguruara', value: ns.length, sub: ns.filter(n => n.public).length + ' publike · ' + ns.filter(n => !n.active).length + ' jashtë shërbimi', icon: 'solar:server-linear' },
    { label: 'Online', value: by('online'), sub: 'brenda ' + st.onlineMult + ' intervaleve', icon: 'solar:check-circle-linear', color: 'var(--green-600)' },
    { label: 'Me vonesë', value: by('delayed'), sub: 'mbi ' + st.onlineMult + ' intervale', icon: 'solar:clock-circle-linear', color: by('delayed') ? '#9A5B00' : null },
    { label: 'Offline', value: by('offline'), sub: 'mbi ' + st.delayedMult + ' intervale', icon: 'solar:close-circle-linear', color: by('offline') ? 'var(--danger)' : null },
    { label: 'Nyje me të dhëna të pavlefshme', value: invalid, sub: 'sensorë të ngopur ose sentinel', icon: 'solar:danger-triangle-linear', color: invalid ? '#9A5B00' : null },
    { label: 'Plotësia e të dhënave', value: completeness + '%', sub: 'fusha të vlefshme mbi nyjet aktive', icon: 'solar:database-linear' },
    { label: 'Disponueshmëria', value: availability + '%', sub: 'nyje aktive që raportojnë tani', icon: 'solar:pulse-linear' }
  ]
})

const cityRows = computed(() => {
  const s = snap.value; tick.value
  if (!s) return []
  const ns = scopeNodes()
  const pm25 = Air.paramByKey('pm25'); const pm10 = Air.paramByKey('pm10'); const tmp = Air.paramByKey('tmp')
  const col = (p, v) => v == null ? 'var(--text-tertiary)' : Air.grade(Air.paramByKey(p), v).fg
  return Air.cities().filter(c => ns.some(n => n.city === c)).map(c => {
    const all = ns.filter(n => n.city === c)
    const live = all.filter(n => s.byId[n.id].usable)
    const p25 = scopedAvg(s, all, 'pm25'); const p10 = scopedAvg(s, all, 'pm10'); const tp = scopedAvg(s, all, 'tmp')
    const g = p25 == null ? { key: 'nodata', label: 'Pa të dhëna', fg: '', bg: '' } : Air.grade(pm25, p25)
    return {
      name: c,
      nodes: live.length + ' / ' + all.length,
      pm25: p25 == null ? '-' : Air.fmtVal(pm25, p25),
      pm10: p10 == null ? '-' : Air.fmtVal(pm10, p10),
      tmp: tp == null ? '-' : Air.fmtVal(tmp, tp) + '°',
      pm25Col: col('pm25', p25), pm10Col: col('pm10', p10), tmpCol: col('tmp', tp),
      grade: g.label,
      gradeTone: GRADE_TONE[g.key] || 'neutral',
      gradeFg: g.fg, gradeBg: g.bg
    }
  })
})

const cityNote = computed(() =>
  'Mesataret llogariten vetëm mbi nyjet që kanë raportuar brenda ' + Air.config.settings.validityMin +
  ' minutave dhe që kalojnë kontrollet e vlefshmërisë. Nyjet me vlera sentinel ose sensorë të ngopur përjashtohen.')

const paramTiles = computed(() => {
  const s = snap.value; tick.value
  if (!s) return []
  const ns = scopeNodes()
  return Air.publicParams().map(p => {
    const v = scopedAvg(s, ns, p.key)
    const okN = ns.filter(n => { const x = s.byId[n.id]; return x && x.usable && x.values[p.key] != null && !x.invalid[p.key] }).length
    return {
      label: p.label, icon: p.icon, unit: p.unit,
      value: v == null ? '-' : Air.fmtVal(p, v),
      color: v == null ? 'var(--text-tertiary)' : Air.colorFor(p, v),
      sub: okN + ' nyje të vlefshme'
    }
  })
})

</script>
