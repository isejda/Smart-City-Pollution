<template>
  <div
    id="adm-scrim"
    :data-open="state.navOpen ? '1' : '0'"
    style="position:fixed;inset:0;z-index:1350;background:rgba(10,13,18,.45)"
    @click="state.navOpen = false"
  ></div>

  <aside
    id="adm-side"
    :data-open="state.navOpen ? '1' : '0'"
    class="sc"
    style="background:#0B1E28;color:rgba(255,255,255,.72);display:flex;flex-direction:column;overflow-y:auto"
  >
    <div style="display:flex;align-items:center;gap:10px;padding:18px 16px 16px">
      <svg width="34" height="34" viewBox="0 0 40 40" fill="none" style="flex-shrink:0" aria-hidden="true">
        <g transform="rotate(128 20 20)">
          <circle cx="20" cy="20" r="16.4" stroke="#FFFFFF" stroke-opacity=".24" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="80 23"></circle>
          <circle cx="20" cy="20" r="9.7" stroke="#7ED0C2" stroke-opacity=".62" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="47 14"></circle>
        </g>
        <circle cx="20" cy="20" r="3.9" fill="#7ED0C2"></circle>
      </svg>
      <div style="line-height:1;min-width:0">
        <div style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-sm);letter-spacing:-.03em;color:#fff">Smart City</div>
        <div style="font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:.2em;margin-top:3px;color:#7ED0C2">POLLUTION</div>
      </div>
    </div>

    <nav style="display:flex;flex-direction:column;gap:2px;padding:6px 10px" aria-label="Seksionet e panelit">
      <button
        v-for="it in nav"
        :key="it.key"
        class="adm-nav-btn"
        :class="{ on: it.on }"
        :aria-current="it.on ? 'page' : 'false'"
        @click="store.go(it.key)"
      >
        <AppIcon :icon="it.icon" :width="17" />
        <span style="flex:1;text-align:left">{{ it.label }}</span>
        <span v-if="it.badge" class="adm-nav-badge">{{ it.badge }}</span>
      </button>
    </nav>

    <div style="margin-top:auto;padding:14px 14px 16px;border-top:1px solid rgba(255,255,255,.08)">
      <div style="font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:rgba(255,255,255,.35);margin-bottom:8px">BURIMI I TË DHËNAVE</div>
      <div style="display:flex;align-items:flex-start;gap:7px;font-size:var(--fs-xs);color:#fff;font-weight:var(--fw-semibold);line-height:var(--lh-heading)">
        <span style="margin-top:5px;width:7px;height:7px;border-radius:50%;flex-shrink:0;background:var(--green-500)"></span>{{ srcLabel }}
      </div>
      <div style="font-size:var(--fs-2xs);line-height:var(--lh-base);color:rgba(255,255,255,.42);margin-top:5px">{{ srcDetail }}</div>
      <a
        href="#/"
        style="display:flex;align-items:center;gap:7px;margin-top:12px;font-size:var(--fs-xs);font-weight:var(--fw-semibold);color:rgba(255,255,255,.62)"
        @click.prevent="openPublic"
      >
        <AppIcon icon="solar:square-top-down-linear" :width="14" />Hap portalin publik
      </a>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '../../components/AppIcon.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, state, tick } = store
const router = useRouter()

const nav = computed(() => {
  // eslint-disable-next-line no-unused-expressions
  tick.value; state.rev
  const items = [
    ['overview', 'Përmbledhje', 'solar:widget-5-linear', null],
    ['map', 'Harta operative', 'solar:map-linear', null],
    ['nodes', 'Nyjet', 'solar:server-linear', Air.config.nodes.length],
    ['params', 'Parametrat', 'solar:tuning-2-linear', Air.config.params.length],
    ['reports', 'Raportet', 'solar:chart-square-linear', null],
    ['settings', 'Burimi & cilësimet', 'solar:settings-linear', null]
  ]
  return items.map(([key, label, icon, badge]) => ({
    key, label, icon, badge: badge || 0, on: state.section === key
  }))
})

const srcLabel = computed(() => { tick.value; return Air.source().label })
const srcDetail = computed(() => (Air.DS.first || '') + ' → ' + (Air.DS.last || ''))

function openPublic () { router.push('/') }
</script>

<style scoped>
.adm-nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 38px;
  padding: 0 11px;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  font-family: var(--font-body);
  font-size: var(--fs-sm);
  font-weight: var(--fw-medium);
  transition: all 140ms;
  background: transparent;
  color: rgba(255, 255, 255, .66);
}
.adm-nav-btn:hover { background: rgba(255, 255, 255, .07); color: #fff; }
.adm-nav-btn.on { background: var(--teal-400); color: #fff; font-weight: var(--fw-semibold); }
.adm-nav-badge {
  min-width: 20px;
  height: 19px;
  padding: 0 6px;
  border-radius: var(--radius-pill);
  font-size: var(--fs-2xs);
  font-weight: var(--fw-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, .1);
  color: rgba(255, 255, 255, .6);
}
.adm-nav-btn.on .adm-nav-badge { background: rgba(255, 255, 255, .22); color: #fff; }
</style>
