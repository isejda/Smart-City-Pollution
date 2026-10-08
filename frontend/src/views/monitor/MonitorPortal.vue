<template>
  <div class="theme-admin adm-root" style="min-height:100vh;display:flex;background:var(--surface-page);font-family:var(--font-body);color:var(--text-primary);font-size:var(--fs-sm)">
    <AdminSidebar />

    <main style="flex:1;min-width:0;display:flex;flex-direction:column">
      <AdminHeader />
      <div class="adm-pad" style="flex:1;padding:22px">
        <component :is="sectionComponent" />
      </div>
    </main>

    <MonitorDrawer />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AdminSidebar from './AdminSidebar.vue'
import AdminHeader from './AdminHeader.vue'
import MonitorDrawer from './MonitorDrawer.vue'
import OverviewSection from './OverviewSection.vue'
import MapSection from './MapSection.vue'
import NodesSection from './NodesSection.vue'
import ParamsSection from './ParamsSection.vue'
import SettingsSection from './SettingsSection.vue'
import ReportsSection from './ReportsSection.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { state } = store

const SECTIONS = {
  overview: OverviewSection,
  map: MapSection,
  nodes: NodesSection,
  params: ParamsSection,
  settings: SettingsSection,
  reports: ReportsSection
}
const sectionComponent = computed(() => SECTIONS[state.section] || OverviewSection)
</script>

<style>
.adm-root #adm-side { width: 242px; flex-shrink: 0; }
.adm-tabs {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.adm-tabs::-webkit-scrollbar { display: none; }
.adm-tabs > * { min-width: max-content; }
.adm-root #adm-scrim { display: none; }

@media (max-width: 1000px) {
  .adm-root #adm-side {
    position: fixed; left: 0; top: 0; bottom: 0; z-index: 1400;
    transform: translateX(-100%);
    transition: transform 240ms cubic-bezier(.32, .72, 0, 1);
  }
  .adm-root #adm-side[data-open="1"] { transform: translateX(0); }
  .adm-root #adm-scrim[data-open="1"] { display: block; }
  #adm-burger { display: flex !important; }
  .adm-kpi { grid-template-columns: repeat(2, 1fr) !important; }
  .adm-2col { grid-template-columns: 1fr !important; }
  .adm-drawer {
    width: 100% !important;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
    top: auto !important; height: 88vh !important;
  }
  .adm-hide-sm { display: none !important; }
  .adm-pad { padding: 16px !important; }
}
@media (max-width: 820px) {
  .adm-kpi { grid-template-columns: 1fr 1fr !important; }
  .adm-hide-xs { display: none !important; }
  .adm-sub { font-size: var(--fs-2xs) !important; }
  .adm-pad { padding: 14px !important; }
  .adm-scope { padding: 9px 14px !important; gap: 8px !important; }
  .adm-scope-lbl { display: none !important; }
  .adm-scope-txt { display: none !important; }
  .adm-scope-sel { flex: 1 1 44% !important; width: auto !important; min-width: 0; }
  .adm-scope-modes { width: 100% !important; margin-left: 0 !important; }
  .adm-tabs { flex: 1 1 100%; }
  /* tables become labelled cards - no sideways scrolling on a phone */
  .adm-tbl-wrap { overflow-x: visible !important; }
  .adm-tbl { min-width: 0 !important; }
  .adm-tbl [role="row"]:first-child { display: none !important; }
  .adm-tbl [role="row"] {
    grid-template-columns: 1fr !important;
    gap: 5px !important; padding: 14px 16px !important; align-items: stretch !important;
  }
  .adm-tbl [role="cell"] {
    display: flex !important; align-items: center; justify-content: space-between;
    gap: 14px; text-align: left !important; min-width: 0;
  }
  .adm-tbl [role="cell"][data-col]:before {
    content: attr(data-col); flex-shrink: 0;
    font-size: var(--fs-2xs); font-weight: var(--fw-bold);
    letter-spacing: var(--ls-wide); color: var(--text-tertiary);
  }
  .adm-tbl [role="cell"]:first-child { display: block !important; margin-bottom: 3px; }
  .adm-tbl [role="cell"]:first-child:before { display: none; }
  .adm-act { width: 100% !important; margin-left: 0 !important; }
  .adm-act button { width: 100% !important; justify-content: center; }
  .adm-drawer { overflow-x: hidden !important; }
}
</style>
