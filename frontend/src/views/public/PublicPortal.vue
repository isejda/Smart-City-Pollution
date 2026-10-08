<template>
  <div class="pp">
    <SiteNav @staff="staffOpen = true" />

    <HeroSection />

    <MapSection />

    <TrendsSection ref="trendsRef" />

    <AdviceSection />

    <AboutSection />

    <SiteFooter />

    <StaffLoginModal :open="staffOpen" @close="staffOpen = false" />
  </div>
</template>

<script setup>
/* ==========================================================================
   PublicPortal - the "Portali publik" view. Ports the original vanilla page
   into idiomatic Vue components while reusing the framework-agnostic
   window.Air engine through the useAir() composable. A single reactive `ui`
   object holds every cross-section selection (map city/param, open node,
   trends scope, advice city, hero slide) and is provided to the children so
   the node drawer can drive the trends section, etc.
   ========================================================================== */
import { reactive, ref, provide, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAir } from '../../composables/useAir.js'
import { buildQuery, parseQuery, sameManaged } from './deeplink.js'
import './public.css'

import SiteNav from './SiteNav.vue'
import HeroSection from './HeroSection.vue'
import MapSection from './MapSection.vue'
import TrendsSection from './TrendsSection.vue'
import AdviceSection from './AdviceSection.vue'
import AboutSection from './AboutSection.vue'
import SiteFooter from './SiteFooter.vue'
import StaffLoginModal from './StaffLoginModal.vue'

const { play, Air, lang, setLang } = useAir()
const route = useRoute()
const router = useRouter()

// Shared UI state - mirrors the original page's `UI` object.
const ui = reactive({
  city: 'Tiranë',
  param: 'pm25',
  panels: true,
  node: null,
  trCity: 'Tiranë',
  trNode: 'city',
  trParam: 'pm25',
  trMode: 'day',
  adCity: 'Tiranë',
  slide: 0
})
provide('ui', ui)

const trendsRef = ref(null)
const staffOpen = ref(false)

// Lets the node drawer jump into the trends section after seeding its scope.
function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
provide('scrollToSection', scrollToSection)

function onKey(e) {
  if (e.key === 'Escape') { ui.node = null; staffOpen.value = false }
}

/* ---------------------------------------------------------------- deep links
   Two-way sync between the shared UI selection and the #/ query string so a
   view is shareable/restorable. `applying` guards the state -> URL writer while
   the URL -> state hydration mutates `ui`, so the two never chase each other. */
let applying = false

function writeUrl() {
  if (applying) return
  const q = buildQuery(route.query, { city: ui.city, param: ui.param, node: ui.node, lang: lang.value })
  if (sameManaged(route.query, q)) return          // nothing managed changed -> skip
  router.replace({ query: q }).catch(() => {})     // replace: keep history clean
}

function hydrateFromUrl() {
  const p = parseQuery(Air, route.query)
  if (p.city) ui.city = p.city
  if (p.param) ui.param = p.param
  if (p.lang === 'en') setLang('en')
  if (p.node) {
    ui.node = p.node                               // opens the NodeDrawer (bound to ui.node)
    // Make sure the linked node is on-screen: switch to its city if needed.
    if (ui.city !== '*' && p.nodeCity && p.nodeCity !== ui.city) ui.city = p.nodeCity
    setTimeout(() => scrollToSection('harta'), 200)
  }
}

onMounted(() => {
  // The original autoplays the replay clock so the hero feed feels live.
  play()
  document.addEventListener('keydown', onKey)
  // Push managed selections into the URL as they change (guarded during hydrate).
  watch(() => [ui.city, ui.param, ui.node, lang.value], writeUrl)
  // Apply the URL once, on mount only, then canonicalise it a single time.
  applying = true
  hydrateFromUrl()
  nextTick(() => { applying = false; writeUrl() })

  // The router redirects here with ?staff=1 when a visit to /monitorimi needs sign-in.
  if (route.query.staff === '1') {
    staffOpen.value = true
    const { staff, ...rest } = route.query
    router.replace({ query: rest }).catch(() => {})
  }
})
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<style scoped>
.pp { display: block; }
</style>
