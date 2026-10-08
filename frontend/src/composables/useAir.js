/* ==========================================================================
   useAir - reactive bridge to the framework-agnostic window.Air engine.
   --------------------------------------------------------------------------
   The engine (air-core.js/air-extra.js) is plain JS with its own clock. This
   composable exposes a single reactive snapshot that both portals derive
   from, plus a language ref. On every replay tick we recompute the snapshot,
   then bump `tick` so label-only computeds refresh too.
   ========================================================================== */
import { shallowRef, ref } from 'vue'

const Air = window.Air

const snap = shallowRef(null)      // latest Air.snapshot() for Air.clock.t
const tick = ref(0)                // bumps on every clock tick / lang change
const lang = ref(Air ? Air.lang : 'sq')
const playing = ref(Air ? Air.clock.playing : false)

let started = false

function refresh() {
  if (!Air) return
  snap.value = Air.snapshot()
  tick.value++
}

function start() {
  if (started || !Air) return
  started = true
  Air.clock.on(function (t, kind) {
    if (kind === 'state') { playing.value = Air.clock.playing; return }
    refresh()
  })
  refresh()
}

export function useAir() {
  start()

  function setLang(l) {
    if (!Air) return
    Air.setLang(l)
    lang.value = Air.lang
    tick.value++
  }

  return {
    Air,
    snap,
    tick,
    lang,
    playing,
    refresh,
    setLang,
    t: (k) => (Air ? Air.t(k) : k),
    play: () => Air && Air.clock.play(),
    pause: () => Air && Air.clock.pause(),
    toggle: () => Air && Air.clock.toggle(),
    seek: (ms) => Air && Air.clock.set(ms)
  }
}
