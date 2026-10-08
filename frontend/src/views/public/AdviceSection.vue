<template>
  <section class="sec" id="keshilla">
    <div class="wrap">
      <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;margin-bottom:20px">
        <div>
          <span class="eyebrow" style="color:var(--teal-500)">
            <AppIcon icon="solar:health-linear" :width="14" />
            <span>{{ lang === 'en' ? 'HEALTH GUIDANCE' : 'UDHËZIME SHËNDETËSORE' }}</span>
          </span>
          <h2 style="font-size:29px;margin-top:9px">{{ t('ad_title') }}</h2>
          <p class="lede" style="margin-top:8px">{{ t('ad_sub') }}</p>
        </div>
        <div class="seg" id="adCityTabs" role="group">
          <button v-for="c in cities" :key="c" :class="{ on: ui.adCity === c }" @click="ui.adCity = c">{{ Air.cityName(c) }}</button>
        </div>
      </div>

      <div style="margin-bottom:16px">
        <div class="card" style="padding:19px 21px;display:flex;align-items:center;gap:22px;flex-wrap:wrap">
          <div style="display:flex;align-items:center;gap:14px">
            <div :style="{ width: '64px', height: '64px', borderRadius: '17px', background: v.aqi.bg, border: '1px solid ' + v.aqi.color + '33', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }">
              <span style="font-family:var(--font-display);font-size:21px;font-weight:600" :style="{ color: v.aqi.color }">{{ v.aqi.v == null ? '-' : v.aqi.v }}</span>
              <span style="font-size:8.5px;font-weight:700;letter-spacing:.08em" :style="{ color: v.aqi.color }">AQI</span>
            </div>
            <div>
              <div style="font-size:11px;font-weight:700;letter-spacing:.06em;color:var(--text-tertiary)">{{ t('now_in').toUpperCase() }} {{ Air.cityName(ui.adCity).toUpperCase() }}</div>
              <div style="font-family:var(--font-display);font-size:21px;font-weight:600;margin-top:2px" :style="{ color: v.aqi.color }">{{ Air.L(v.aqi.label) }}</div>
              <div style="font-size:11.5px;color:var(--text-tertiary);margin-top:2px">{{ v.liveCount }} {{ lang === 'en' ? 'nodes reporting' : 'nyje po raportojnë' }} · {{ Air.fmtDateTimeL(v.time) }}</div>
            </div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-left:auto">
            <div v-for="c in v.params" :key="c.p.key" style="border:1px solid var(--border-subtle);border-radius:9px;padding:7px 11px;min-width:76px">
              <div style="font-size:9.5px;font-weight:700;color:var(--text-tertiary);letter-spacing:.04em">{{ Air.tp(c.p, 'label').toUpperCase() }}</div>
              <div style="font-family:var(--font-display);font-size:15px;font-weight:600;margin-top:2px" :style="{ color: c.v == null ? 'var(--text-disabled)' : Air.colorFor(c.p, c.v) }">{{ Air.fmtVal(c.p, c.v) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid3" id="adCards" style="grid-template-columns:repeat(auto-fit,minmax(250px,1fr))">
        <div v-for="a in v.cards" :key="a.k" class="card lift" style="padding:19px 21px;display:flex;flex-direction:column;gap:11px">
          <div style="display:flex;align-items:center;gap:10px">
            <div :style="{ width: '36px', height: '36px', borderRadius: '10px', background: v.aqi.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }">
              <AppIcon :icon="a.ad.icon" :width="19" :style="{ color: v.aqi.color }" />
            </div>
            <h3 style="font-size:14.5px">{{ a.ad.label }}</h3>
          </div>
          <p style="font-size:13.5px;line-height:1.6;color:var(--text-secondary)">{{ a.ad.text }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'

const { Air, snap, lang, tick, t } = useAir()
const ui = inject('ui')

const cities = ['Tiranë', 'Korçë', 'Elbasan']

function isLive(s) { return s && s.node.active && (s.status === 'online' || s.status === 'delayed') }

const v = computed(() => {
  void tick.value; void lang.value
  const s = snap.value
  const pm = s ? Air.cityAvg(s, ui.adCity, 'pm25') : null
  const aqi = Air.aqi(pm)
  const active = Air.config.nodes.filter((n) => n.public && n.city === ui.adCity && n.active)
  const liveCount = active.filter((n) => isLive(s && s.byId[n.id])).length
  const params = Air.publicParams().map((p) => ({ p, v: s ? Air.cityAvg(s, ui.adCity, p.key) : null }))
  const cards = ['all', 'kids', 'old', 'sport', 'asthma'].map((k) => ({ k, ad: Air.adviceFor(k, aqi.lvl) }))
  return { aqi, liveCount, params, cards, time: s ? s.t : Air.clock.t }
})
</script>
