<template>
  <section class="sec" id="trendet" style="background:#F3F7F6;border-top:1px solid var(--border-subtle);border-bottom:1px solid var(--border-subtle)">
    <div class="wrap">
      <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;margin-bottom:20px">
        <div>
          <span class="eyebrow" style="color:var(--teal-500)">
            <AppIcon icon="solar:chart-2-linear" :width="14" />
            <span>{{ lang === 'en' ? 'HISTORY & FORECAST' : 'HISTORIKU & PARASHIKIMI' }}</span>
          </span>
          <h2 style="font-size:29px;margin-top:9px">{{ t('tr_title') }}</h2>
          <p class="lede" style="margin-top:8px">{{ t('tr_sub') }}</p>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end" id="trControls">
          <div class="fld">
            <label>{{ t('city') }}</label>
            <select class="sel" v-model="ui.trCity" @change="ui.trNode = 'city'">
              <option v-for="c in cities" :key="c" :value="c">{{ Air.cityName(c) }}</option>
            </select>
          </div>
          <div class="fld">
            <label>{{ t('node') }}</label>
            <select class="sel" style="max-width:220px" v-model="ui.trNode">
              <option value="city">{{ t('city_avg') }} ({{ nodeList.length }})</option>
              <option v-for="n in nodeList" :key="n.id" :value="n.id">{{ n.name }}</option>
            </select>
          </div>
          <div class="fld">
            <label>{{ t('param') }}</label>
            <select class="sel" v-model="ui.trParam">
              <option v-for="p in paramList" :key="p.key" :value="p.key">{{ Air.tp(p, 'label') }}</option>
            </select>
          </div>
          <div class="fld">
            <label>{{ t('period') }}</label>
            <div class="seg" style="height:36px;align-items:center">
              <button v-for="m in ['day','week','month']" :key="m" :class="{ on: ui.trMode === m }" @click="ui.trMode = m">{{ Air.modeLabel(m) }}</button>
            </div>
          </div>
        </div>
      </div>

      <div class="grid2">
        <div class="card" style="padding:18px 20px 14px;overflow:hidden">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-bottom:12px">
            <div>
              <div style="display:flex;align-items:center;gap:8px">
                <span style="width:10px;height:10px;border-radius:3px" :style="{ background: Air.paramColor(v.p, v.scopeNode) }"></span>
                <h3 style="font-size:16px">{{ Air.tp(v.p, 'label') }} - {{ v.scopeLbl }}</h3>
              </div>
              <div style="font-size:12px;color:var(--text-tertiary);margin-top:4px">{{ Air.modeSub(ui.trMode) }} · {{ Air.tp(v.p, 'unit') }} · {{ v.ids.length }} {{ lang === 'en' ? 'node(s)' : 'nyje' }}</div>
            </div>
            <div style="display:flex;align-items:center;gap:14px;font-size:11px;color:var(--text-tertiary)">
              <span style="display:flex;align-items:center;gap:5px"><i style="width:14px;height:2.5px;display:block;border-radius:2px" :style="{ background: Air.paramColor(v.p, v.scopeNode) }"></i>{{ t('observed') }}</span>
            </div>
          </div>
          <div v-html="v.chart"></div>
        </div>

        <div style="display:flex;flex-direction:column;gap:14px">
          <div class="card" style="padding:16px 18px">
            <div style="font-size:10.5px;font-weight:700;letter-spacing:.07em;color:var(--text-tertiary);margin-bottom:10px">{{ lang === 'en' ? 'PERIOD SUMMARY' : 'PËRMBLEDHJE E PERIUDHËS' }}</div>
            <div v-for="x in v.summary" :key="x[0]" class="kv"><span>{{ x[0] }}</span><b>{{ Air.fmtVal(v.p, x[1]) }} {{ Air.tp(v.p, 'unit') }}</b></div>
            <div class="kv"><span>{{ lang === 'en' ? 'Trend' : 'Ecuria' }}</span><b :style="{ color: v.delta == null ? 'var(--text-tertiary)' : v.delta > 0 ? '#B1322F' : '#1F8A4C' }">{{ v.deltaText }}</b></div>
            <div class="kv"><span>{{ lang === 'en' ? 'Valid points' : 'Pika të vlefshme' }}</span><b>{{ v.valid }} / {{ v.total }}</b></div>
          </div>

          <div class="card" style="padding:16px 18px">
            <template v-if="v.fc">
              <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:10px">
                <div style="font-size:10.5px;font-weight:700;letter-spacing:.07em;color:var(--text-tertiary)">{{ t('forecast_72').toUpperCase() }}</div>
                <span v-if="v.fc.source === 'model'" class="chip" style="background:#EAF0FE;color:#4976F4" :title="v.fc.modelName || ''">
                  <AppIcon icon="solar:cpu-bolt-linear" :width="12" /> {{ lang === 'en' ? 'AI model' : 'Model AI' }}
                </span>
                <span v-else class="chip" style="background:var(--teal-100);color:var(--teal-500)">{{ v.fc.fut[23].conf }}% {{ t('conf') }}</span>
              </div>
              <div v-html="v.fcSpark"></div>
              <div style="display:flex;gap:6px;margin-top:10px">
                <div v-for="dd in v.days" :key="dd.t" style="flex:1;border:1px solid var(--border-subtle);border-radius:8px;padding:8px 7px;text-align:center">
                  <div style="font-size:9.5px;font-weight:700;color:var(--text-tertiary);letter-spacing:.04em">{{ Air.fmtDayShort(dd.t).toUpperCase() }}</div>
                  <div style="font-family:var(--font-display);font-size:15px;font-weight:600;margin-top:3px" :style="{ color: Air.colorFor(v.p, dd.avg) }">{{ Air.fmtVal(v.p, dd.avg) }}</div>
                  <div style="font-size:9.5px;color:var(--text-tertiary);margin-top:1px">{{ Air.fmtVal(v.p, dd.min) }}–{{ Air.fmtVal(v.p, dd.max) }}</div>
                </div>
              </div>
              <div style="margin-top:10px;padding-top:9px;border-top:1px solid var(--border-subtle);font-size:11.5px;color:var(--text-secondary);display:flex;gap:7px;align-items:flex-start">
                <span style="color:var(--teal-500);flex-shrink:0"><AppIcon icon="solar:clock-circle-linear" :width="14" /></span>
                <span v-if="v.bw && v.bw.betterThanNow">{{ t('best_window') }}: <b>{{ Air.fmtDayShort(v.bw.from) }} {{ Air.fmtTime(v.bw.from) }}–{{ Air.fmtTime(v.bw.to) }}</b></span>
                <span v-else>{{ t('best_none') }}</span>
              </div>
            </template>
            <div v-else style="font-size:12.5px;color:var(--text-tertiary)">{{ t('no_data') }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject, watchEffect } from 'vue'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'
import { chartSVG, spark } from './chart.js'

const { Air, snap, lang, tick, t } = useAir()
const ui = inject('ui')

function cityList() { return ['Tiranë', 'Korçë', 'Elbasan'] }
function pubNodes() { return Air.config.nodes.filter((n) => n.public) }
function activeIn(c) { return pubNodes().filter((n) => (c === '*' || n.city === c) && n.active) }

const cities = cityList()
const paramList = computed(() => { void lang.value; return Air.publicParams() })
const nodeList = computed(() => { void lang.value; return activeIn(ui.trCity) })

// mirror the original guard: drop to city-average when the picked node isn't
// an active node of the selected city.
watchEffect(() => {
  if (ui.trNode !== 'city' && !activeIn(ui.trCity).some((n) => n.id === ui.trNode)) ui.trNode = 'city'
})

const v = computed(() => {
  void tick.value; void lang.value
  const t0 = snap.value ? snap.value.t : Air.clock.t
  const p = Air.paramByKey(ui.trParam)
  const ids = ui.trNode === 'city' ? activeIn(ui.trCity).map((n) => n.id) : [ui.trNode]
  const scopeNode = ui.trNode === 'city' ? null : Air.nodeById(ui.trNode)
  const scopeLbl = ui.trNode === 'city'
    ? (Air.cityName(ui.trCity) + ' · ' + t('city_avg').toLowerCase())
    : scopeNode.name
  const tr = Air.trend(ids, ui.trParam, ui.trMode, t0)
  const chart = chartSVG({ points: tr.points, param: p, node: scopeNode, w: 840, h: 270, id: 'tr' })
  const summary = [[t('avg'), tr.avg], [t('min'), tr.min], [t('max'), tr.max]]
  const delta = tr.delta
  const deltaText = delta == null ? '-' : (delta > 0 ? '▲ +' : '▼ ') + Air.fmtVal(p, Math.abs(delta)) + ' ' + Air.tp(p, 'unit')

  const fc = Air.forecast(ids, ui.trParam, t0, 72)
  const days = fc ? Air.dayOutlook(fc) : []
  const bw = fc ? Air.bestWindow(fc) : null
  const fcSpark = fc ? spark(fc.fut.map((x) => ({ t: x.t, v: x.v })), p, scopeNode, 300, 54) : ''

  return { p, ids, scopeNode, scopeLbl, chart, summary, delta, deltaText, valid: tr.valid, total: tr.points.length, fc, days, bw, fcSpark }
})
</script>
