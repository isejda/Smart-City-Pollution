<template>
  <footer>
    <div class="wrap">
      <div style="display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:36px" id="footGrid">
        <div>
          <span v-html="brand"></span>
          <p style="font-size:12.5px;line-height:1.65;margin-top:14px;max-width:34ch">{{ excerpt(t('ab_b'), 148) }}</p>
        </div>
        <div class="fcol">
          <span class="fh">{{ t('ft_portal').toUpperCase() }}</span>
          <a v-for="l in links" :key="l.id" :href="'#' + l.id" @click.prevent="scrollToSection(l.id)">{{ t(l.key) }}</a>
        </div>
        <div class="fcol">
          <span class="fh">{{ t('ft_data').toUpperCase() }}</span>
          <span>{{ t('ft_source') }}: {{ Air.DS.source || '-' }}</span>
          <span>{{ t('ft_range') }}: {{ (st.first || '').slice(0, 10) }} → {{ (st.last || '').slice(0, 10) }}</span>
          <span>{{ num(st.rows) }} {{ t('stat_rows') }}</span>
          <span>{{ t('ft_tz') }}: Europe/Tirane</span>
        </div>
        <div class="fcol">
          <span class="fh">{{ t('ft_contact').toUpperCase() }}</span>
          <a href="mailto:info@smartcitypollution.al">info@smartcitypollution.al</a>
          <span>{{ lang === 'en' ? 'Tirana, Albania' : 'Tiranë, Shqipëri' }}</span>
        </div>
      </div>
      <div style="margin-top:38px;padding-top:18px;border-top:1px solid rgba(255,255,255,.1);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-size:11.5px;color:rgba(255,255,255,.4)" id="footBot">
        <span>© 2026 Smart City Pollution · {{ t('ft_rights') }}</span>
        <span>{{ t('replay_note') }}</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed, inject } from 'vue'
import { useAir } from '../../composables/useAir.js'
import { num, excerpt } from './helpers.js'

const { Air, lang, tick, t } = useAir()
const scrollToSection = inject('scrollToSection')

const links = [
  { id: 'harta', key: 'nav_map' },
  { id: 'trendet', key: 'nav_trends' },
  { id: 'keshilla', key: 'nav_advice' },
  { id: 'projekti', key: 'nav_about' }
]

const brand = computed(() => { void tick.value; return Air.logoLockup({ size: 34, fs: 15, onDark: true }) })
const st = computed(() => { void tick.value; return Air.networkStats() })
</script>
