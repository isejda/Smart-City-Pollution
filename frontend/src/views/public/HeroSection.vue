<template>
  <section
    class="hero"
    id="projekti-hero"
    :class="{ paused }"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
  >
    <div class="hero-wm" v-html="watermark"></div>
    <div class="hero-in">
      <!-- copy -->
      <div class="hero-copy">
        <div class="fadein" :key="ui.slide">
          <div style="display:flex;align-items:center;gap:11px;margin-bottom:2px">
            <span class="eyebrow" style="color:#7ED0C2">{{ pad2(ui.slide + 1) }} / {{ pad2(slides.length) }}</span>
            <span style="width:24px;height:1px;background:rgba(255,255,255,.26)"></span>
            <span class="eyebrow" style="color:rgba(255,255,255,.5)">{{ t(slides[ui.slide].eb) }}</span>
          </div>
          <h1>{{ t(slides[ui.slide].t) }}</h1>
          <p>{{ fill(t(slides[ui.slide].b)) }}</p>
          <div class="heroCta" style="display:flex;gap:10px;margin-top:26px;flex-wrap:wrap">
            <a href="#harta" class="btn btn-teal" style="background:#0E6A60" @click.prevent="goTo('harta')">
              <AppIcon icon="solar:map-linear" :width="16" />{{ t('hero_cta_map') }}
            </a>
            <a href="#projekti" class="btn" style="border-color:rgba(255,255,255,.22);color:#fff" @click.prevent="goTo('projekti')">{{ t('hero_cta_learn') }}</a>
          </div>
        </div>
      </div>

      <!-- chapters -->
      <div class="chapters">
        <section
          v-for="(s, i) in slides"
          :key="i"
          class="ch"
          :class="{ on: i === ui.slide }"
        >
          <button class="ch-b" :aria-expanded="i === ui.slide" :aria-label="t(s.eb)" @click="goSlide(i)">
            <span class="ch-g"><AppIcon :icon="s.ic" :width="19" /></span>
            <span class="ch-i">{{ pad2(i + 1) }}</span>
            <span class="ch-t">{{ t(s.short || s.eb) }}</span>
            <span class="ch-k">{{ s.meta() }}</span>
          </button>
          <div class="ch-p"><i v-if="i === ui.slide" :key="progKey"></i></div>
          <div class="ch-body" v-if="i === ui.slide" v-html="currentPane"></div>
        </section>
      </div>

      <!-- mobile pane -->
      <div class="hero-pane">
        <div class="hero-pane-in" :key="ui.slide" v-html="currentPane"></div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, inject, onMounted, onUnmounted } from 'vue'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'
import { num, fill, pad2 } from './helpers.js'
import { esc } from './chart.js'

const { Air, snap, lang, tick, t } = useAir()
const ui = inject('ui')
const scrollToSection = inject('scrollToSection')

function pubNodes() { return Air.config.nodes.filter((n) => n.public) }
function cities() { return ['Tiranë', 'Korçë', 'Elbasan'] }
function pubParams() { return Air.publicParams() }
function nodeSnap(id) { return snap.value && snap.value.byId[id] }
function isLive(s) { return s && s.node.active && (s.status === 'online' || s.status === 'delayed') }

/* -------- panes (return HTML strings, rendered via v-html) -------- */
function paneStats() {
  var st = Air.networkStats()
  var cells = [[st.active, t('stat_nodes')], [cities().length, t('stat_cities')],
    [num(st.rows), t('stat_rows')], [pubParams().length, t('stat_params')]]
  return '<div style="display:grid;grid-template-columns:1fr 1fr;height:100%">' + cells.map(function (c, i) {
    var b = (i < 2 ? 'border-bottom:1px solid rgba(255,255,255,.09);' : '') + (i % 2 === 0 ? 'border-right:1px solid rgba(255,255,255,.09);' : '')
    return '<div class="st" style="' + b + 'display:flex;flex-direction:column;justify-content:center"><b' + (String(c[0]).length > 6 ? ' style="font-size:21px"' : '') + '>' + esc(String(c[0])) + '</b><span>' + esc(c[1]) + '</span></div>'
  }).join('') + '</div>'
}

function paneCoverage() {
  var p = Air.paramByKey('pm25'), v = Air.cityAvg(snap.value, 'Tiranë', 'pm25')
  var col = v == null ? '#7ED0C2' : Air.colorFor(p, v), g = ''
  for (var x = 40; x < 560; x += 56) g += '<line x1="' + x + '" y1="0" x2="' + x + '" y2="150" stroke="#fff" stroke-opacity=".05"/>'
  for (var y = 22; y < 150; y += 32) g += '<line x1="0" y1="' + y + '" x2="560" y2="' + y + '" stroke="#fff" stroke-opacity=".05"/>'
  return '<svg viewBox="0 0 560 150" preserveAspectRatio="xMidYMid meet" style="width:100%;height:150px;display:block" role="img" aria-label="' + esc(t('cov_title')) + '">' + g +
      '<circle cx="98" cy="44" r="21" fill="#fff" fill-opacity=".03" stroke="#fff" stroke-opacity=".22" stroke-width="1.2" stroke-dasharray="4 4"/><circle cx="98" cy="44" r="2.6" fill="#fff" fill-opacity=".4"/>' +
      '<circle cx="466" cy="110" r="21" fill="#fff" fill-opacity=".03" stroke="#fff" stroke-opacity=".22" stroke-width="1.2" stroke-dasharray="4 4"/><circle cx="466" cy="110" r="2.6" fill="#fff" fill-opacity=".4"/>' +
      '<circle cx="280" cy="74" r="44" fill="' + col + '" fill-opacity=".2" stroke="' + col + '" stroke-opacity=".7" stroke-width="1.5"/>' +
      '<circle cx="280" cy="74" r="4.8" fill="' + col + '"/>' +
      '<line x1="280" y1="74" x2="324" y2="74" stroke="' + col + '" stroke-opacity=".65" stroke-width="1" stroke-dasharray="3 3"/>' +
      '<text x="302" y="68" text-anchor="middle" font-size="9" font-weight="700" fill="' + col + '" font-family="var(--font-body)">150 m</text>' +
      '<text x="280" y="134" text-anchor="middle" font-size="10.5" font-weight="700" fill="#fff" font-family="var(--font-body)">' + Air.fmtVal(p, v) + ' µg/m³</text>' +
    '</svg>' +
    '<div style="display:flex;gap:14px;flex-wrap:wrap;padding:9px 15px;border-top:1px solid rgba(255,255,255,.09);font-size:11px;color:rgba(255,255,255,.5)">' +
      '<span style="display:flex;align-items:center;gap:6px"><i style="width:9px;height:9px;border-radius:50%;background:' + col + ';display:block"></i>' + esc(t('cov_measured')) + '</span>' +
      '<span style="display:flex;align-items:center;gap:6px"><i style="width:9px;height:9px;border-radius:50%;border:1px dashed rgba(255,255,255,.45);display:block"></i>' + esc(t('cov_nosensor')) + '</span>' +
      '<span style="margin-left:auto">' + esc(t('cov_foot')) + '</span></div>'
}

function paneFeed() {
  var p = Air.paramByKey('pm25')
  var rows = pubNodes().map(function (n) { return { n: n, s: nodeSnap(n.id) } })
    .filter(function (x) { return x.s && x.s.packetAt })
    .sort(function (a, b) { return b.s.packetAt - a.s.packetAt }).slice(0, 4)
  return rows.map(function (x, i) {
    var v = x.s.values.pm25; if (v != null && x.s.invalid.pm25) v = null
    return '<div class="frow"' + (i === 0 ? ' style="border-top:none"' : '') + '><i style="width:7px;height:7px;border-radius:50%;flex-shrink:0;background:' + (isLive(x.s) ? '#22A65A' : '#B1322F') + '"></i>' +
        '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600">' + esc(x.n.name.split('-')[0].trim()) + '</span>' +
        '<span style="color:rgba(255,255,255,.42);font-size:11px;flex-shrink:0">' + esc(Air.fmtAgeL(x.s.ageMs)) + '</span>' +
        '<span style="flex-shrink:0;font-weight:700;font-size:11px;padding:3px 9px;border-radius:100px;min-width:54px;text-align:center;color:#fff;background:' + (v == null ? 'rgba(255,255,255,.12)' : Air.colorFor(p, v)) + '">' + Air.fmtVal(p, v) + '</span></div>'
  }).join('') +
    '<div style="padding:10px 15px;border-top:1px solid rgba(255,255,255,.09);font-size:11px;color:rgba(255,255,255,.42)">' + esc(t('feed_note')) + ' · ' + esc(Air.fmtTime(snap.value.t)) + '</div>'
}

function paneGoal() {
  var steps = [['step1_t', 'step1_b'], ['step2_t', 'step2_b'], ['step3_t', 'step3_b']]
  var pad = ' style="padding:14px 15px"'
  return steps.map(function (s, i) {
    return '<div class="step"' + (i === 0 ? ' style="border-top:none;padding:14px 15px"' : pad) + '><u>' + (i + 1) + '</u><span style="min-width:0">' +
        '<span style="display:block;font-size:13px;font-weight:600">' + esc(t(s[0])) + '</span>' +
        '<span style="display:block;font-size:11.5px;color:rgba(255,255,255,.55);margin-top:2px;line-height:1.5">' + esc(t(s[1])) + '</span></span></div>'
  }).join('')
}

const slides = [
  { eb: 'h1_eyebrow', t: 'h1_t', b: 'h1_b', pane: paneStats, ic: 'solar:wind-linear', meta: () => Air.networkStats().active + ' ' + t('stat_nodes') },
  { eb: 'h2_eyebrow', t: 'h2_t', b: 'h2_b', pane: paneCoverage, ic: 'solar:map-point-wave-linear', meta: () => '~150 m' },
  { eb: 'h3_eyebrow', t: 'h3_t', b: 'h3_b', pane: paneFeed, ic: 'solar:database-linear', short: 'h3_short', meta: () => num(Air.networkStats().rows) },
  { eb: 'h4_eyebrow', t: 'h4_t', b: 'h4_b', pane: paneGoal, ic: 'solar:target-linear', meta: () => '3 ' + (lang.value === 'en' ? 'steps' : 'hapa') }
]

const watermark = computed(() => { void tick.value; return Air.logoMark(420, '#7ED0C2', '#7ED0C2') })
const currentPane = computed(() => {
  void tick.value; void lang.value
  if (!snap.value) return ''
  return slides[ui.slide].pane()
})

/* -------- auto-advance / interaction -------- */
const paused = ref(false)
const progKey = ref(0)
let timer = null
let tx = null

function restart() {
  clearInterval(timer)
  timer = setInterval(() => goSlide(ui.slide + 1), 9000)
}
function goSlide(i) {
  ui.slide = (i + slides.length) % slides.length
  progKey.value++
  restart()
}
function goTo(id) { scrollToSection(id) }
function onEnter() { paused.value = true; clearInterval(timer) }
function onLeave() { paused.value = false; restart() }
function onTouchStart(e) { tx = e.touches[0].clientX }
function onTouchEnd(e) {
  if (tx == null) return
  var dx = e.changedTouches[0].clientX - tx; tx = null
  if (Math.abs(dx) > 52) goSlide(ui.slide + (dx < 0 ? 1 : -1))
}

onMounted(restart)
onUnmounted(() => clearInterval(timer))
</script>
