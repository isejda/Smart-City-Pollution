<template>
  <aside class="drawer" :class="{ open: !!nodeId }" aria-label="node details">
    <template v-if="d">
      <div style="display:flex;align-items:flex-start;gap:10px;padding:16px 18px 12px;border-bottom:1px solid var(--border-subtle)">
        <div :style="{ width: '11px', height: '11px', borderRadius: '50%', background: d.stColor, marginTop: '6px', flexShrink: 0 }"></div>
        <div style="flex:1;min-width:0">
          <h3 style="font-size:15.5px;line-height:1.25">{{ d.n.name }}</h3>
          <div style="font-size:11.5px;color:var(--text-tertiary);margin-top:3px">
            {{ Air.cityName(d.n.city) }} · {{ d.n.id }} · <b :style="{ color: d.stColor, fontWeight: 700 }">{{ d.stLbl }}</b>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm" style="padding:0;width:32px" :aria-label="t('close')" @click="$emit('close')">
          <AppIcon icon="solar:close-circle-linear" :width="17" />
        </button>
      </div>

      <div class="dr-body">
        <!-- big latest reading -->
        <div style="display:flex;align-items:flex-end;gap:12px;padding:16px 0 14px">
          <div :style="{ width: '52px', height: '52px', borderRadius: '13px', background: d.main == null ? '#F2F2F2' : Air.colorFor(d.p, d.main), display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }">
            <AppIcon :icon="d.p.icon" :width="26" style="color:#fff" />
          </div>
          <div style="flex:1;min-width:0">
            <div style="font-size:11px;font-weight:700;letter-spacing:.06em;color:var(--text-tertiary)">{{ Air.tp(d.p, 'label').toUpperCase() }}</div>
            <div style="display:flex;align-items:baseline;gap:6px;margin-top:2px">
              <span style="font-family:var(--font-display);font-size:30px;font-weight:600;letter-spacing:-.02em">{{ Air.fmtVal(d.p, d.main) }}</span>
              <span style="font-size:12px;color:var(--text-tertiary);font-weight:600">{{ Air.tp(d.p, 'unit') }}</span>
            </div>
          </div>
          <span class="chip" :style="{ background: d.gr.bg, color: d.gr.fg }">{{ Air.L(d.gr.label) }}</span>
        </div>

        <div style="font-size:11px;color:var(--text-tertiary);margin-bottom:12px">
          {{ t('updated') }} {{ d.s.packetAt ? Air.fmtAgeL(d.s.ageMs) + ' ' + t('ago') : '-' }} · {{ Air.fmtDateTimeL(d.s.packetAt || snap.t) }}
        </div>

        <!-- param grid -->
        <div class="vgrid" style="margin-bottom:16px">
          <div v-for="q in d.np" :key="q.key" class="vcell">
            <u>{{ Air.tp(q, 'label') }}</u>
            <b :style="{ color: qVal(q) == null ? 'var(--text-disabled)' : Air.colorFor(q, qVal(q)) }">{{ Air.fmtVal(q, qVal(q)) }}</b>
            <s>{{ Air.tp(q, 'unit') }}</s>
          </div>
        </div>

        <!-- trend -->
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;flex-wrap:wrap">
          <h4 style="font-size:13px">{{ Air.tp(d.p, 'label') }} · {{ Air.modeSub(mode) }}</h4>
          <div class="seg">
            <button
              v-for="m in ['day','week','month']"
              :key="m"
              :class="{ on: mode === m }"
              style="height:26px;padding:0 10px;font-size:11.5px"
              @click="mode = m"
            >{{ Air.modeLabel(m) }}</button>
          </div>
        </div>
        <div style="margin:0 -6px 4px" v-html="d.chart"></div>
        <div style="display:flex;gap:8px;margin-bottom:18px">
          <div v-for="x in d.mma" :key="x[0]" style="flex:1;border:1px solid var(--border-subtle);border-radius:8px;padding:7px 9px">
            <div style="font-size:9.5px;font-weight:700;letter-spacing:.05em;color:var(--text-tertiary)">{{ x[0] }}</div>
            <div style="font-family:var(--font-display);font-size:14px;font-weight:600;margin-top:2px">{{ Air.fmtVal(d.p, x[1]) }}</div>
          </div>
        </div>

        <!-- 72h forecast -->
        <template v-if="d.fc">
          <h4 style="font-size:13px;margin-bottom:8px">{{ t('forecast_72') }}</h4>
          <div style="border:1px solid var(--border-subtle);border-radius:10px;padding:10px 12px 8px;margin-bottom:16px">
            <div v-html="d.fcSpark"></div>
            <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-tertiary);margin-top:4px">
              <span>{{ Air.fmtTime(d.fc.fut[0].t) }}</span><span>+72h</span>
            </div>
            <div v-if="d.bw" style="display:flex;gap:7px;align-items:flex-start;margin-top:9px;padding-top:9px;border-top:1px solid var(--border-subtle);font-size:11.5px;color:var(--text-secondary)">
              <span style="color:var(--teal-500);flex-shrink:0"><AppIcon icon="solar:clock-circle-linear" :width="14" /></span>
              <span>{{ t('best_window') }}: <b style="font-weight:700">{{ Air.fmtDayShort(d.bw.from) }} {{ Air.fmtTime(d.bw.from) }}–{{ Air.fmtTime(d.bw.to) }}</b> · {{ Air.fmtVal(d.p, d.bw.val) }} {{ Air.tp(d.p, 'unit') }}</span>
            </div>
          </div>
        </template>

        <!-- health advice -->
        <div :style="{ display: 'flex', gap: '9px', alignItems: 'flex-start', background: d.aqi.bg, borderRadius: '10px', padding: '11px 13px', marginBottom: '16px' }">
          <span :style="{ color: d.aqi.color, flexShrink: 0 }"><AppIcon icon="solar:health-linear" :width="17" /></span>
          <div>
            <div :style="{ fontSize: '11px', fontWeight: 700, color: d.aqi.color }">{{ Air.L(d.aqi.label) }}{{ d.aqi.v != null ? ' · AQI ' + d.aqi.v : '' }}</div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:3px;line-height:1.5">{{ d.ad.text }}</div>
          </div>
        </div>

        <!-- node facts -->
        <h4 style="font-size:13px;margin-bottom:6px">{{ lang === 'en' ? 'Node details' : 'Detajet e nyjes' }}</h4>
        <div style="margin-bottom:14px">
          <div v-for="r in d.rows" :key="r[0]" class="kv"><span>{{ r[0] }}</span><b>{{ r[1] }}</b></div>
        </div>

        <button class="btn btn-teal" style="width:100%" @click="openTrends">
          <AppIcon icon="solar:chart-2-linear" :width="15" />{{ t('open_trends') }}
        </button>
      </div>
    </template>
  </aside>
</template>

<script setup>
import { computed, ref, inject, watch } from 'vue'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'
import { chartSVG, spark } from './chart.js'

const props = defineProps({ nodeId: { type: String, default: null } })
defineEmits(['close'])

const { Air, snap, lang, tick, t } = useAir()
const ui = inject('ui')
const scrollToSection = inject('scrollToSection')

const mode = ref('day')
const shownId = ref(props.nodeId)
watch(() => props.nodeId, (v) => { if (v) shownId.value = v })

function isLive(s) { return s && s.node.active && (s.status === 'online' || s.status === 'delayed') }
function nodeSnap(id) { return snap.value && snap.value.byId[id] }

function qVal(q) {
  const s = nodeSnap(shownId.value)
  const live = isLive(s)
  let v = live ? s.values[q.key] : null
  if (v != null && s.invalid[q.key]) v = null
  return v
}

const d = computed(() => {
  void tick.value; void lang.value; void mode.value
  const id = shownId.value
  if (!id || !snap.value) return null
  const n = Air.nodeById(id)
  const s = nodeSnap(id)
  if (!n || !s) return null
  const live = isLive(s)
  const p = Air.paramByKey(ui.param)
  const stColor = n.active ? (live ? '#22A65A' : '#F79009') : '#B1322F'
  const stLbl = n.active ? (live ? t('active') : Air.L(Air.STATUS[s.status].label)) : t('inactive')

  let main = live ? s.values[ui.param] : null
  if (main != null && s.invalid[ui.param]) main = null
  const gr = Air.grade(p, main)
  const np = Air.nodeParams(n, true)

  const tr = Air.trend([n.id], ui.param, mode.value, snap.value.t)
  const chart = chartSVG({ points: tr.points, param: p, node: n, w: 400, h: 170, id: 'dr' })
  const mma = [[t('min').toUpperCase(), tr.min], [t('avg').toUpperCase(), tr.avg], [t('max').toUpperCase(), tr.max]]

  const fc = Air.forecast([n.id], ui.param, snap.value.t, 72)
  const bw = fc ? Air.bestWindow(fc) : null
  const fcSpark = fc ? spark(fc.fut.map((x) => ({ t: x.t, v: x.v })), p, n, 340, 52) : ''

  const aqi = Air.aqi(live ? s.values.pm25 : null)
  const ad = Air.adviceFor('all', aqi.lvl)

  const rows = [
    [t('address'), n.address],
    [t('tech'), Air.techLabel(n.tech)],
    [t('interval'), n.intervalS >= 60 ? (Math.round(n.intervalS / 6) / 10) + ' min' : n.intervalS + ' s'],
    [t('installed'), Air.fmtDateL(Air.parseTs(n.installedAt + ' 00:00:00')) + ' ' + String(n.installedAt).slice(0, 4)],
    [lang.value === 'en' ? 'Coverage' : 'Mbulimi', '~' + (n.coverageM || 150) + ' m']
  ]

  return { n, s, p, stColor, stLbl, main, gr, np, chart, mma, fc, bw, fcSpark, aqi, ad, rows }
})

function openTrends() {
  const n = d.value.n
  ui.trCity = n.city
  ui.trNode = n.id
  ui.trParam = ui.param
  scrollToSection('trendet')
}
</script>
