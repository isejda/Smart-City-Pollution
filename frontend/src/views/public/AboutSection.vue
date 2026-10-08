<template>
  <section class="sec" id="projekti" style="background:#F3F7F6;border-top:1px solid var(--border-subtle)">
    <div class="wrap">
      <div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:44px;align-items:start" id="aboutGrid">
        <div>
          <span class="eyebrow" style="color:var(--teal-500)">
            <AppIcon icon="solar:buildings-2-linear" :width="14" />
            <span>{{ t('nav_about').toUpperCase() }}</span>
          </span>
          <h2 style="font-size:29px;margin-top:9px">{{ t('ab_title') }}</h2>
          <p class="lede" style="margin-top:12px">{{ t('ab_b') }}</p>
          <div style="display:flex;gap:10px;margin-top:20px;flex-wrap:wrap">
            <div v-for="tech in techs" :key="tech.k" class="card" style="padding:13px 15px;display:flex;gap:10px;align-items:flex-start;max-width:280px">
              <AppIcon :icon="tech.icon" :width="19" style="color:var(--teal-500);margin-top:1px" />
              <div>
                <div style="font-size:13px;font-weight:600">{{ Air.techLabel(tech.k) }}</div>
                <div style="font-size:11.5px;color:var(--text-tertiary);margin-top:2px;line-height:1.5">{{ tech.hint }}</div>
              </div>
            </div>
          </div>
          <div style="display:flex;gap:9px;align-items:flex-start;margin-top:18px;padding:13px 15px;border:1px solid var(--border-subtle);border-radius:10px;background:var(--surface-card)">
            <AppIcon icon="solar:info-circle-linear" :width="16" style="color:var(--amber-500);margin-top:1px" />
            <p style="font-size:12px;line-height:1.6;color:var(--text-secondary)">{{ t('disclaimer') }}</p>
          </div>
        </div>

        <div>
          <h3 style="font-size:17px;margin-bottom:14px">{{ t('ab_what') }}</h3>
          <div style="display:flex;flex-direction:column;gap:8px">
            <div v-for="c in params" :key="c.p.key" class="card lift" style="padding:14px 16px;display:flex;gap:13px;align-items:center">
              <div :style="{ width: '34px', height: '34px', borderRadius: '9px', background: Air.paramColor(c.p) + '1a', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }">
                <AppIcon :icon="c.p.icon" :width="18" :style="{ color: Air.paramColor(c.p) }" />
              </div>
              <div style="flex:1;min-width:0">
                <div style="font-size:13.5px;font-weight:600">{{ Air.tp(c.p, 'long') }}</div>
                <div style="font-size:11.5px;color:var(--text-tertiary);margin-top:2px;line-height:1.5">{{ Air.tp(c.p, 'desc') }}</div>
              </div>
              <div style="text-align:right;flex-shrink:0">
                <div style="font-family:var(--font-display);font-size:16px;font-weight:600">{{ Air.fmtVal(c.p, c.v) }}</div>
                <div style="font-size:10px;color:var(--text-tertiary)">{{ Air.tp(c.p, 'unit') }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'

const { Air, snap, lang, tick, t } = useAir()

const techs = computed(() => {
  void lang.value
  return Object.keys(Air.TECHS).map((k) => {
    const tech = Air.TECHS[k]
    return { k, icon: tech.icon, hint: lang.value === 'en' ? tech.hint[1] : tech.hint[0] }
  })
})

const params = computed(() => {
  void tick.value; void lang.value
  const s = snap.value
  return Air.publicParams().map((p) => ({ p, v: s ? Air.netAvg(s, p.key) : null }))
})
</script>
