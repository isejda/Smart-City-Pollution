<template>
  <header class="nav" :class="{ up: scrolled }">
    <div class="nav-in">
      <a href="#" style="flex-shrink:0" @click.prevent="toTop" v-html="brand"></a>
      <nav class="navlinks">
        <a
          v-for="l in links"
          :key="l.id"
          class="navlink"
          :class="{ on: active === l.id }"
          :href="'#' + l.id"
          @click.prevent="go(l.id)"
        >{{ t(l.key) }}</a>
      </nav>
      <div style="margin-left:auto;display:flex;align-items:center;gap:10px">
        <div class="lang" role="group" aria-label="Language">
          <button :class="{ on: lang === 'sq' }" @click="setLang('sq')">SQ</button>
          <button :class="{ on: lang === 'en' }" @click="setLang('en')">EN</button>
        </div>
        <button class="btn btn-ghost" @click="$emit('staff')">
          <AppIcon icon="solar:lock-keyhole-minimalistic-linear" :width="15" />
          <span class="hide-sm">{{ t('staff_login') }}</span>
        </button>
        <button class="burger" aria-label="Menu" @click="mobOpen = !mobOpen">
          <AppIcon icon="solar:hamburger-menu-linear" :width="20" />
        </button>
      </div>
    </div>
    <div
      v-show="mobOpen"
      style="border-top:1px solid var(--border-subtle);padding:10px 16px 14px;flex-direction:column;gap:4px;background:#fff;display:flex"
    >
      <a
        v-for="l in links"
        :key="l.id"
        class="navlink"
        :href="'#' + l.id"
        style="display:flex;align-items:center;gap:11px;padding:12px 6px;font-size:15px;font-weight:600;border-bottom:1px solid var(--border-subtle)"
        @click.prevent="go(l.id); mobOpen = false"
      >
        <AppIcon :icon="l.icon" :width="18" style="color:var(--teal-500)" />{{ t(l.key) }}
      </a>
      <a
        class="navlink"
        href="#"
        style="display:flex;align-items:center;gap:11px;padding:12px 6px;font-size:15px;font-weight:600"
        @click.prevent="mobOpen = false"
      >
        <AppIcon icon="solar:smartphone-linear" :width="18" style="color:var(--teal-500)" />{{ lang === 'en' ? 'Mobile app' : 'Aplikacioni mobil' }}
      </a>
    </div>
  </header>
</template>

<script setup>
import { computed, ref, inject, onMounted, onUnmounted } from 'vue'
import { useAir } from '../../composables/useAir.js'
import AppIcon from '../../components/AppIcon.vue'

const { Air, lang, tick, t, setLang } = useAir()
const scrollToSection = inject('scrollToSection')

defineEmits(['staff'])

const links = [
  { id: 'harta', key: 'nav_map', icon: 'solar:map-point-wave-linear' },
  { id: 'trendet', key: 'nav_trends', icon: 'solar:chart-2-linear' },
  { id: 'keshilla', key: 'nav_advice', icon: 'solar:health-linear' },
  { id: 'projekti', key: 'nav_about', icon: 'solar:buildings-2-linear' }
]

const brand = computed(() => { void tick.value; return Air.logoLockup({ size: 34, fs: 15 }) })

const mobOpen = ref(false)
const scrolled = ref(false)
const active = ref('')

function go(id) { scrollToSection(id) }
function toTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }

let raf = null
function onScroll() {
  if (raf) return
  raf = requestAnimationFrame(() => {
    raf = null
    scrolled.value = window.scrollY > 8
    const y = window.scrollY + 120
    let cur = ''
    links.forEach((l) => {
      const el = document.getElementById(l.id)
      if (el && el.offsetTop <= y) cur = l.id
    })
    active.value = cur
  })
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>
