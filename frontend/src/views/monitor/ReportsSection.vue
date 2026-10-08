<template>
  <div style="display:flex;flex-direction:column;gap:16px">
    <!-- KPI cards -->
    <div class="adm-kpi" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
      <div v-for="(k, i) in repKpis" :key="i" style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:14px 16px;box-shadow:var(--shadow-xs)">
        <div style="display:flex;align-items:flex-start;gap:7px;font-size:var(--fs-xs);font-weight:var(--fw-medium);line-height:var(--lh-heading);color:var(--text-tertiary);min-height:32px">
          <AppIcon :icon="k.icon" :width="14" :style="{ flexShrink: 0, marginTop: '2px', color: k.iconColor }" />{{ k.label }}
        </div>
        <div style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-h2);letter-spacing:var(--ls-tight);margin-top:6px" :style="k.valueColor ? { color: k.valueColor } : {}">{{ k.value }}</div>
        <div style="font-size:var(--fs-xs);color:var(--text-tertiary);margin-top:2px">{{ k.sub }}</div>
      </div>
    </div>

    <!-- per-node data volume -->
    <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
      <div style="display:flex;align-items:center;gap:9px;padding:14px 18px;border-bottom:1px solid var(--border-subtle);flex-wrap:wrap">
        <AppIcon icon="solar:database-linear" :width="16" style="color:var(--teal-500)" />
        <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Sa të dhëna kemi për secilën nyje</h2>
        <span style="margin-left:auto;font-size:var(--fs-xs);color:var(--text-tertiary)">{{ scopeText }}</span>
      </div>
      <div class="adm-tbl-wrap">
        <div class="adm-tbl" role="table" aria-label="Vëllimi i të dhënave sipas nyjes" style="font-size:var(--fs-xs)">
          <div role="row" style="display:grid;grid-template-columns:2fr .9fr 1fr 1.5fr .6fr .8fr 1.1fr .9fr;gap:8px;padding:10px 16px;background:var(--surface-subtle);font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary)">
            <span role="columnheader">NYJA</span>
            <span role="columnheader">QYTETI</span>
            <span role="columnheader" style="text-align:right">MATJE</span>
            <span role="columnheader">PERIUDHA</span>
            <span role="columnheader" style="text-align:right">DITË</span>
            <span role="columnheader" style="text-align:right">INTERVAL</span>
            <span role="columnheader">VËLLIMI</span>
            <span role="columnheader" style="text-align:right">NDËRPRERJE</span>
          </div>
          <div v-for="r in repRows" :key="r.id" role="row" class="adm-tbl-row" style="display:grid;grid-template-columns:2fr .9fr 1fr 1.5fr .6fr .8fr 1.1fr .9fr;gap:8px;align-items:center;padding:11px 16px;border-top:1px solid var(--border-subtle);cursor:pointer" @click="r.open()">
            <span role="cell" data-col="NYJA" style="min-width:0">
              <span style="display:block;font-weight:var(--fw-semibold);font-size:var(--fs-sm)">{{ r.name }}</span>
              <span style="display:block;font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:2px">{{ r.tech }}</span>
            </span>
            <span role="cell" data-col="QYTETI" style="color:var(--text-secondary)">{{ r.city }}</span>
            <span role="cell" data-col="MATJE" style="text-align:right;font-weight:var(--fw-semibold)">{{ r.rows }}</span>
            <span role="cell" data-col="PERIUDHA" style="color:var(--text-secondary);font-size:var(--fs-2xs)">{{ r.period }}</span>
            <span role="cell" data-col="DITË" style="text-align:right;color:var(--text-secondary)">{{ r.days }}</span>
            <span role="cell" data-col="INTERVAL" style="text-align:right;color:var(--text-secondary)">{{ r.interval }}</span>
            <span role="cell" data-col="VËLLIMI" style="display:flex;align-items:center;gap:7px">
              <span style="flex:1;height:6px;border-radius:var(--radius-pill);background:var(--surface-muted);overflow:hidden;display:block"><i :style="r.bar"></i></span>
              <span style="font-size:var(--fs-2xs);font-weight:var(--fw-semibold);color:var(--text-tertiary)">{{ r.share }}</span>
            </span>
            <span role="cell" data-col="NDËRPRERJE" style="text-align:right" :style="{ color: r.gapColor, fontWeight: r.gapBold ? 'var(--fw-semibold)' : 'normal' }">{{ r.gaps }}</span>
          </div>
        </div>
      </div>
      <div style="padding:12px 18px;border-top:1px solid var(--border-subtle);background:var(--surface-subtle);font-size:var(--fs-xs);color:var(--text-tertiary);line-height:var(--lh-base)">{{ repNote }}</div>
    </section>

    <div class="adm-2col" style="display:grid;grid-template-columns:1.3fr 1fr;gap:16px;align-items:start">
      <!-- trend chart -->
      <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
        <div style="display:flex;align-items:center;gap:9px;padding:14px 18px;border-bottom:1px solid var(--border-subtle);flex-wrap:wrap">
          <AppIcon icon="solar:chart-2-linear" :width="16" style="color:var(--teal-500)" />
          <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">{{ repChartTitle }}</h2>
          <div style="margin-left:auto">
            <span class="adm-tabs">
              <DsTabs variant="pill" :items="repParamItems" :model-value="state.mapParam" @update:model-value="v => state.mapParam = v" />
            </span>
          </div>
        </div>
        <div style="padding:16px 18px">
          <svg viewBox="0 0 300 92" preserveAspectRatio="none" width="100%" height="180" style="display:block" role="img" :aria-label="repChartTitle">
            <path :d="repChart.area" :fill="repChart.color" opacity=".15"></path>
            <path :d="repChart.line" fill="none" :stroke="repChart.color" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"></path>
          </svg>
          <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:var(--fs-2xs);color:var(--text-tertiary)">
            <span>{{ repChart.x0 }}</span><span>{{ repChart.sub }}</span><span>{{ repChart.x1 }}</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px">
            <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:8px 10px">
              <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">MIN</div>
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold);margin-top:2px">{{ repChart.statMin }}</div>
            </div>
            <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:8px 10px">
              <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">MESATARE</div>
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold);margin-top:2px">{{ repChart.statAvg }}</div>
            </div>
            <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:8px 10px">
              <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">MAKS</div>
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold);margin-top:2px">{{ repChart.statMax }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- param coverage -->
      <section style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-md);box-shadow:var(--shadow-xs);overflow:hidden">
        <div style="display:flex;align-items:center;gap:9px;padding:14px 18px;border-bottom:1px solid var(--border-subtle)">
          <AppIcon icon="solar:checklist-minimalistic-linear" :width="16" style="color:var(--teal-500)" />
          <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-base);margin:0">Mbulimi i parametrave</h2>
        </div>
        <div style="padding:14px 18px;display:flex;flex-direction:column;gap:11px">
          <div v-for="p in repParams" :key="p.label">
            <div style="display:flex;align-items:baseline;justify-content:space-between;gap:10px;font-size:var(--fs-xs);margin-bottom:5px">
              <span style="font-weight:var(--fw-semibold)">{{ p.label }}</span>
              <span style="color:var(--text-tertiary)">{{ p.detail }}</span>
            </div>
            <span style="display:block;height:7px;border-radius:var(--radius-pill);background:var(--surface-muted);overflow:hidden"><i :style="p.bar"></i></span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import DsTabs from '../../components/ui/DsTabs.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, tick, state, scopeNodes, scopeLabel } = store

const repNote = 'Numrat vijnë nga eksporti i dataset-it, jo nga pozicioni i replay-t: ata tregojnë sa të dhëna ka realisht secila nyje. “Vëllimi” është pesha e nyjes ndaj totalit të zgjedhur.'

// day/week/month series → one SVG path pair (300×92 user units)
function lineBlock (nodes, key, mode) {
  const p = Air.paramByKey(key)
  const tr = Air.trend(nodes.map(n => n.id), key, mode, Air.clock.t)
  const W = 300; const H = 92; const top = 6; const bot = 6
  const vals = tr.points.filter(d => d.v != null).map(d => d.v)
  const color = Air.paramColor(p, nodes.length === 1 ? nodes[0] : null)
  const base = { color, sub: Air.modeSub(mode) + ' · ' + tr.valid + '/' + tr.points.length + ' pika', line: '', area: '', x0: '', x1: '', statMin: '-', statAvg: '-', statMax: '-' }
  if (!vals.length) { base.sub = 'pa të dhëna në këtë periudhë'; return base }
  let lo = Math.min.apply(null, vals); let hi = Math.max.apply(null, vals)
  const padv = (hi - lo) * 0.16 || Math.max(0.5, Math.abs(hi) * 0.08)
  lo -= padv; hi += padv
  const X = i => (tr.points.length < 2 ? W / 2 : i * W / (tr.points.length - 1))
  const Y = v => top + (H - top - bot) - (v - lo) / ((hi - lo) || 1) * (H - top - bot)
  let line = ''; let firstX = null; let lastX = 0
  tr.points.forEach((d, i) => {
    if (d.v == null) return
    const x = X(i); const y = Y(d.v)
    line += (firstX === null ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
    if (firstX === null) firstX = x
    lastX = x
  })
  base.line = line
  base.area = line + 'L' + lastX.toFixed(1) + ',' + H + 'L' + (firstX || 0).toFixed(1) + ',' + H + 'Z'
  base.x0 = tr.points[0] ? tr.points[0].label : ''
  base.x1 = tr.points[tr.points.length - 1] ? tr.points[tr.points.length - 1].label : ''
  base.statMin = Air.fmtVal(p, tr.min); base.statAvg = Air.fmtVal(p, tr.avg); base.statMax = Air.fmtVal(p, tr.max)
  return base
}

const model = computed(() => {
  tick.value; state.rev
  const ns = scopeNodes()
  const stats = ns.map(n => ({ n, s: Air.nodeStats(n) }))
  const totalRows = stats.reduce((t, x) => t + x.s.rows, 0)
  const maxRows = stats.reduce((t, x) => Math.max(t, x.s.rows), 1)
  const totalGaps = stats.reduce((t, x) => t + x.s.gaps1h, 0)
  const allDays = {}
  stats.forEach(x => { if (x.s.first && x.s.last) { allDays[x.s.first.slice(0, 10)] = 1; allDays[x.s.last.slice(0, 10)] = 1 } })
  const spanFrom = Object.keys(allDays).sort()[0] || '-'
  const spanTo = Object.keys(allDays).sort().slice(-1)[0] || '-'
  const avgDays = stats.length ? Math.round(stats.reduce((t, x) => t + x.s.days, 0) / stats.length) : 0
  return { ns, stats, totalRows, maxRows, totalGaps, spanFrom, spanTo, avgDays }
})

const repKpis = computed(() => {
  const m = model.value
  return [
    { label: 'Matje gjithsej', value: m.totalRows.toLocaleString('de-DE'), sub: scopeLabel(), icon: 'solar:database-linear', iconColor: 'var(--teal-500)' },
    { label: 'Periudha e mbuluar', value: m.spanFrom.slice(5) + ' → ' + m.spanTo.slice(5), sub: 'mesatarisht ' + m.avgDays + ' ditë për nyje', icon: 'solar:calendar-linear', iconColor: 'var(--teal-500)' },
    { label: 'Ndërprerje mbi 1 orë', value: m.totalGaps, sub: 'gjithsej në nyjet e zgjedhura', icon: 'solar:link-broken-linear', iconColor: m.totalGaps ? '#9A5B00' : 'var(--text-tertiary)', valueColor: m.totalGaps ? '#9A5B00' : '' }
  ]
})

const repRows = computed(() => {
  const m = model.value
  return m.stats.map(({ n, s }) => ({
    id: n.id, name: n.name, city: n.city, tech: Air.techLabel(n.tech),
    rows: s.rows.toLocaleString('de-DE'),
    period: s.first ? s.first.slice(0, 10) + ' → ' + s.last.slice(0, 10) : '-',
    days: s.days,
    interval: s.avgIntervalS >= 60 ? Math.round(s.avgIntervalS / 6) / 10 + ' min' : s.avgIntervalS + ' s',
    share: Math.round(s.rows / (m.totalRows || 1) * 100) + '%',
    bar: 'display:block;height:100%;border-radius:var(--radius-pill);background:var(--teal-400);width:' + Math.round(s.rows / m.maxRows * 100) + '%',
    gaps: s.gaps1h,
    gapColor: s.gaps1h > 20 ? '#9A5B00' : 'var(--text-secondary)',
    gapBold: s.gaps1h > 20,
    open: () => { store.go('nodes'); store.openDrawer({ kind: 'node', id: n.id }, { dtab: 'overview', buf: Air.clone(n) }) }
  }))
})

const scopeText = computed(() => { tick.value; state.rev; return scopeLabel() })
const repChartTitle = computed(() => Air.paramByKey(state.mapParam).label + ' - ' + scopeLabel())
const repParamItems = computed(() => Air.publicParams().map(p => ({ value: p.key, label: p.label })))
const repChart = computed(() => lineBlock(model.value.ns, state.mapParam, state.dmode))

const repParams = computed(() => {
  const acc = {}
  model.value.stats.forEach(({ s }) => s.params.forEach(p => {
    const a = acc[p.key] || (acc[p.key] = { label: p.label, valid: 0, total: 0, color: p.color, nodes: 0 })
    a.valid += p.valid; a.total += p.total; a.nodes++
  }))
  return Object.keys(acc).map(k => {
    const a = acc[k]; const pct = a.total ? a.valid / a.total * 100 : 0
    return {
      label: a.label,
      detail: a.nodes + ' nyje · ' + a.valid.toLocaleString('de-DE') + ' vlera të vlefshme · ' + pct.toFixed(1) + '%',
      bar: 'display:block;height:100%;border-radius:var(--radius-pill);background:' + a.color + ';width:' + pct.toFixed(1) + '%'
    }
  })
})

</script>

<style scoped>
.adm-tbl-row:hover { background: var(--surface-subtle); }
</style>
