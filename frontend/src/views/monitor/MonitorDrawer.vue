<template>
  <div v-if="state.drawer">
    <div style="position:fixed;inset:0;z-index:1500;background:rgba(10,13,18,.45)" @click="store.closeDrawer()"></div>
    <aside class="adm-drawer sc" style="position:fixed;top:0;right:0;bottom:0;width:min(560px,100%);z-index:1510;background:var(--surface-card);box-shadow:-10px 0 40px rgba(10,13,18,.18);display:flex;flex-direction:column;overflow:hidden">
      <div style="display:flex;align-items:flex-start;gap:12px;padding:16px 18px;border-bottom:1px solid var(--border-subtle);flex-shrink:0">
        <div style="min-width:0;flex:1">
          <h2 style="font-family:var(--font-display);font-weight:var(--fw-semibold);font-size:var(--fs-lg);letter-spacing:var(--ls-tight);margin:0">{{ view.title }}</h2>
          <div style="font-size:var(--fs-xs);color:var(--text-tertiary);margin-top:3px">{{ view.sub }}</div>
        </div>
        <DsIconButton variant="ghost" aria-label="Mbyll" @click="store.closeDrawer()">
          <AppIcon icon="solar:close-circle-linear" :width="17" />
        </DsIconButton>
      </div>

      <div v-if="view.tabs.length" style="padding:8px 14px;border-bottom:1px solid var(--border-subtle);overflow-x:auto;flex-shrink:0">
        <DsTabs variant="segment" :items="view.tabs" :model-value="state.dtab || 'overview'" @update:model-value="setDtab" />
      </div>

      <div class="sc" style="flex:1;overflow-y:auto;padding:16px 18px 24px">
        <div v-for="(b, bi) in view.blocks" :key="bi" style="margin-bottom:16px">
          <!-- head -->
          <div v-if="b.type === 'head'" style="font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary);margin-bottom:8px">{{ b.text }}</div>
          <!-- text -->
          <p v-else-if="b.type === 'text'" style="margin:0;font-size:var(--fs-xs);line-height:var(--lh-relaxed);color:var(--text-secondary)">{{ b.text }}</p>
          <!-- note -->
          <div v-else-if="b.type === 'note'" style="display:flex;gap:9px;padding:11px 13px;border-radius:var(--radius-sm);background:var(--surface-subtle);font-size:var(--fs-xs);line-height:var(--lh-base);color:var(--text-secondary)">
            <AppIcon icon="solar:info-circle-linear" :width="15" style="flex-shrink:0;margin-top:1px;color:var(--text-tertiary)" />
            <span>{{ b.text }}</span>
          </div>
          <!-- stats -->
          <div v-else-if="b.type === 'stats'" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px">
            <div v-for="(s, i) in b.items" :key="i" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:9px 11px">
              <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-semibold)">{{ s.k }}</div>
              <div style="font-size:var(--fs-sm);font-weight:var(--fw-semibold);margin-top:3px" :style="s.color ? { color: s.color } : {}">{{ s.v }}</div>
              <div v-if="s.sub" style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:2px">{{ s.sub }}</div>
            </div>
          </div>
          <!-- rows -->
          <div v-else-if="b.type === 'rows'" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);overflow:hidden">
            <div v-for="(r, i) in b.items" :key="i" style="display:flex;align-items:baseline;justify-content:space-between;gap:14px;padding:9px 12px;border-bottom:1px solid var(--surface-subtle);font-size:var(--fs-xs)">
              <span style="color:var(--text-tertiary);flex-shrink:0">{{ r.k }}</span>
              <span style="font-weight:var(--fw-semibold);text-align:right;word-break:break-word" :style="r.color ? { color: r.color } : {}">{{ r.v }}</span>
            </div>
          </div>
          <!-- bars chart -->
          <div v-else-if="b.type === 'chart'" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:12px 13px">
            <div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:8px">
              <span style="font-size:var(--fs-xs);font-weight:var(--fw-semibold)">{{ b.text }}</span>
              <span style="font-size:var(--fs-2xs);color:var(--text-tertiary)">{{ b.sub }}</span>
            </div>
            <svg viewBox="0 0 100 34" preserveAspectRatio="none" width="100%" height="86" style="display:block" role="img" :aria-label="b.text">
              <rect v-for="(s, i) in b.items" :key="i" :x="s.x" :y="s.y" :width="s.w" :height="s.h" :fill="s.c"></rect>
            </svg>
            <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:var(--fs-2xs);color:var(--text-tertiary)">
              <span>{{ b.axisLo }}</span><span>{{ b.axisHi }}</span>
            </div>
          </div>
          <!-- line chart -->
          <div v-else-if="b.type === 'line'" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:12px 13px">
            <div style="display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:8px">
              <span style="font-size:var(--fs-xs);font-weight:var(--fw-semibold)">{{ b.text }}</span>
              <span style="font-size:var(--fs-2xs);color:var(--text-tertiary)">{{ b.sub }}</span>
            </div>
            <svg viewBox="0 0 300 92" preserveAspectRatio="none" width="100%" height="96" style="display:block" role="img" :aria-label="b.text">
              <path :d="b.area" :fill="b.color" opacity=".15"></path>
              <path :d="b.line" fill="none" :stroke="b.color" stroke-width="1.8" vector-effect="non-scaling-stroke" stroke-linejoin="round" stroke-linecap="round"></path>
            </svg>
            <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:var(--fs-2xs);color:var(--text-tertiary)">
              <span>{{ b.x0 }}</span><span>{{ b.x1 }}</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:9px">
              <div v-for="(st, i) in [['MIN', b.statMin], ['MESATARE', b.statAvg], ['MAKS', b.statMax]]" :key="i" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);padding:6px 8px">
                <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-weight:var(--fw-bold)">{{ st[0] }}</div>
                <div style="font-size:var(--fs-xs);font-weight:var(--fw-semibold);margin-top:2px">{{ st[1] }}</div>
              </div>
            </div>
          </div>
          <!-- packets -->
          <div v-else-if="b.type === 'packets'" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);overflow:auto">
            <div role="table" aria-label="Paketat e fundit" style="min-width:440px;font-size:var(--fs-2xs);font-family:ui-monospace,monospace">
              <div role="row" style="display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr 1fr 1fr 1fr;gap:6px;padding:7px 9px;background:var(--surface-subtle);font-weight:var(--fw-bold);color:var(--text-tertiary)">
                <span>ORA</span><span style="text-align:right">PM2.5</span><span style="text-align:right">PM10</span><span style="text-align:right">T°C</span><span style="text-align:right">RH%</span><span style="text-align:right">SND</span><span style="text-align:right">UV</span>
              </div>
              <div v-for="(p, i) in b.items" :key="i" role="row" style="display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr 1fr 1fr 1fr;gap:6px;padding:6px 9px;border-top:1px solid var(--surface-subtle)">
                <span style="color:var(--text-secondary)">{{ p.ts }}</span>
                <span style="text-align:right" :style="p.c25 ? { color: 'var(--text-tertiary)' } : {}">{{ p.pm25 }}</span>
                <span style="text-align:right" :style="p.c10 ? { color: 'var(--text-tertiary)' } : {}">{{ p.pm10 }}</span>
                <span style="text-align:right">{{ p.tmp }}</span>
                <span style="text-align:right">{{ p.hum }}</span>
                <span style="text-align:right">{{ p.snd }}</span>
                <span style="text-align:right">{{ p.uv }}</span>
              </div>
            </div>
          </div>
          <!-- timeline -->
          <div v-else-if="b.type === 'timeline'" style="display:flex;flex-direction:column;gap:0">
            <div v-for="(e, i) in b.items" :key="i" style="display:flex;gap:11px">
              <div style="display:flex;flex-direction:column;align-items:center;flex-shrink:0">
                <span :style="e.dotStyle"></span>
                <span style="flex:1;width:1px;background:var(--border-subtle)"></span>
              </div>
              <div style="padding-bottom:14px;min-width:0">
                <div style="font-size:var(--fs-xs);font-weight:var(--fw-semibold)">{{ e.text }}</div>
                <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:2px">{{ e.when }}</div>
              </div>
            </div>
          </div>
          <!-- param config -->
          <div v-else-if="b.type === 'paramcfg'" style="border:1px solid var(--border-subtle);border-radius:var(--radius-sm);overflow:hidden">
            <div v-for="(pc, i) in b.items" :key="i" style="display:flex;align-items:center;gap:9px;padding:10px 12px;border-bottom:1px solid var(--surface-subtle);flex-wrap:wrap">
              <AppIcon :icon="pc.icon" :width="15" :style="{ color: pc.color, flexShrink: 0 }" />
              <span style="flex:1;min-width:110px">
                <span style="display:block;font-size:var(--fs-xs);font-weight:var(--fw-semibold)">{{ pc.label }}</span>
                <span style="display:block;font-size:var(--fs-2xs);color:var(--text-tertiary)">{{ pc.sub }}</span>
              </span>
              <span style="display:flex;gap:4px">
                <button v-for="(sw, j) in pc.swatches" :key="j" :aria-label="sw.label" :title="sw.label" :style="sw.style" @click="sw.go()"></button>
              </span>
              <DsSwitch :model-value="pc.on" :aria-label="pc.label" @update:model-value="pc.toggle" />
            </div>
          </div>
          <!-- actions -->
          <div v-else-if="b.type === 'actions'" style="display:flex;gap:8px;flex-wrap:wrap">
            <DsButton v-for="(a, i) in b.items" :key="i" :variant="a.variant" size="sm" :leading-icon="a.icon" @click="a.go()">{{ a.label }}</DsButton>
          </div>
          <!-- fields -->
          <div v-else-if="b.type === 'fields'" style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div v-for="(f, i) in b.items" :key="i" :style="f.span2 ? { gridColumn: 'span 2' } : {}">
              <template v-if="f.kind === 'toggle'">
                <div style="display:flex;flex-direction:column;gap:8px;padding-top:4px">
                  <span style="font-size:var(--fs-sm);font-weight:var(--fw-medium)">{{ f.label }}</span>
                  <DsSwitch :model-value="!!state.buf[f.key]" :aria-label="f.label" @update:model-value="state.buf[f.key] = !state.buf[f.key]" />
                  <span v-if="f.hint" style="font-size:var(--fs-xs);color:var(--text-tertiary);line-height:var(--lh-heading)">{{ f.hint }}</span>
                </div>
              </template>
              <template v-else>
                <label style="display:block;font-size:var(--fs-2xs);font-weight:var(--fw-bold);letter-spacing:var(--ls-wide);color:var(--text-tertiary);margin-bottom:5px">{{ f.label }}</label>
                <DsSelect v-if="f.kind === 'select'" :model-value="bufStr(f.key)" :options="f.options" :aria-label="f.label" @update:model-value="v => state.buf[f.key] = v" />
                <textarea v-else-if="f.kind === 'area'" :value="bufStr(f.key)" rows="3" class="adm-textarea" @input="state.buf[f.key] = $event.target.value"></textarea>
                <DsInput v-else :model-value="bufStr(f.key)" :type="f.kind === 'number' ? 'number' : f.kind === 'date' ? 'date' : 'text'" :aria-label="f.label" @update:model-value="v => state.buf[f.key] = v" />
                <div v-if="f.hint" style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:4px;line-height:var(--lh-heading)">{{ f.hint }}</div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <div v-if="view.footer" style="display:flex;gap:9px;padding:13px 18px;border-top:1px solid var(--border-subtle);background:var(--surface-subtle);flex-shrink:0">
        <DsButton variant="secondary" size="md" :full-width="true" @click="store.closeDrawer()">Anulo</DsButton>
        <DsButton variant="accent" size="md" :full-width="true" @click="saveDrawer">{{ view.footer }}</DsButton>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import DsButton from '../../components/ui/DsButton.vue'
import DsIconButton from '../../components/ui/DsIconButton.vue'
import DsTabs from '../../components/ui/DsTabs.vue'
import DsSelect from '../../components/ui/DsSelect.vue'
import DsInput from '../../components/ui/DsInput.vue'
import DsSwitch from '../../components/ui/DsSwitch.vue'
import { useMonitorStore } from './useMonitorStore'

const store = useMonitorStore()
const { Air, snap, tick, state } = store

const bufStr = k => { const v = state.buf ? state.buf[k] : ''; return v == null ? '' : v }
const opts = pairs => pairs.map(([value, label]) => ({ value, label }))

/* ---------- field factories ---------- */
function field (key, label, o = {}) {
  return Object.assign({ key, label, kind: 'text', hint: '', span2: false }, o)
}
function toggleField (key, label, hint) { return { key, label, hint: hint || '', kind: 'toggle', span2: false } }

/* ---------- day/week/month line ---------- */
function lineBlock (nodes, key, mode, title) {
  const p = Air.paramByKey(key)
  const tr = Air.trend(nodes.map(n => n.id), key, mode, Air.clock.t)
  const W = 300; const H = 92; const top = 6; const bot = 6
  const vals = tr.points.filter(d => d.v != null).map(d => d.v)
  const base = {
    type: 'line', text: (title || p.label) + ' · ' + p.unit,
    sub: Air.modeSub(mode) + ' · ' + tr.valid + '/' + tr.points.length + ' pika',
    color: Air.paramColor(p, nodes.length === 1 ? nodes[0] : null),
    line: '', area: '', x0: '', x1: '', statMin: '-', statAvg: '-', statMax: '-'
  }
  if (!vals.length) { base.sub = 'pa të dhëna në këtë periudhë'; return base }
  let lo = Math.min.apply(null, vals); let hi = Math.max.apply(null, vals)
  const padv = (hi - lo) * 0.16 || Math.max(0.5, Math.abs(hi) * 0.08)
  lo -= padv; hi += padv
  const X = i => (tr.points.length < 2 ? W / 2 : i * W / (tr.points.length - 1))
  const Y = v => top + (H - top - bot) - (v - lo) / ((hi - lo) || 1) * (H - top - bot)
  let line = ''; let firstX = null; let lastX = 0
  tr.points.forEach((d, i) => {
    if (d.v == null) return
    const x = X(i); const y = Y(d.v)
    line += (firstX === null ? 'M' : 'L') + x.toFixed(1) + ',' + y.toFixed(1)
    if (firstX === null) firstX = x
    lastX = x
  })
  base.line = line
  base.area = line + 'L' + lastX.toFixed(1) + ',' + H + 'L' + (firstX || 0).toFixed(1) + ',' + H + 'Z'
  base.x0 = tr.points[0] ? tr.points[0].label : ''
  base.x1 = tr.points[tr.points.length - 1] ? tr.points[tr.points.length - 1].label : ''
  base.statMin = Air.fmtVal(p, tr.min); base.statAvg = Air.fmtVal(p, tr.avg); base.statMax = Air.fmtVal(p, tr.max)
  return base
}

/* ---------- per-node parameter set editor ---------- */
function paramCfgBlock () {
  const buf = state.buf || {}
  const setCfg = (k, patch) => {
    buf.params = buf.params || {}
    buf.params[k] = Object.assign({ on: true, color: null }, buf.params[k] || {}, patch)
  }
  const cfg = buf.params || {}
  return {
    type: 'paramcfg',
    items: Air.config.params.map(p => {
      const c = cfg[p.key] || {}
      const on = (buf.sensors || []).indexOf(p.key) >= 0 && c.on !== false
      const cur = c.color || p.color
      const swatches = [p.color, '#08514A', '#B1322F', '#4976F4', '#6D28D9'].map((hex, i) => ({
        label: i === 0 ? 'Ngjyra e parazgjedhur' : hex,
        style: 'width:18px;height:18px;border-radius:5px;cursor:pointer;flex-shrink:0;padding:0;background:' + hex +
          ';border:2px solid ' + (cur === hex ? 'var(--text-primary)' : 'transparent') + ';box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)',
        go: () => setCfg(p.key, { color: i === 0 ? null : hex })
      }))
      return {
        icon: p.icon, color: cur, label: p.label, sub: p.unit + ' · ' + (on ? 'aktiv' : 'i çaktivizuar'),
        swatches, on,
        toggle: () => {
          buf.sensors = (buf.sensors || []).slice()
          const at = buf.sensors.indexOf(p.key)
          if (at >= 0) buf.sensors.splice(at, 1); else buf.sensors.push(p.key)
          buf.params = buf.params || {}
          buf.params[p.key] = Object.assign({ color: null }, buf.params[p.key] || {}, { on: at < 0 })
        }
      }
    })
  }
}

/* ---------- node drawer blocks ---------- */
function nodeBlocks (node) {
  const s = snap.value.byId[node.id]; const st = s ? Air.STATUS[s.status] : null
  const meta = Air.source().meta(node)
  const tab = state.dtab || 'overview'
  const B = []
  if (tab === 'overview') {
    B.push({ type: 'stats', items: [
      { k: 'STATUSI', v: st.label, color: st.fg },
      { k: 'PAKETA E FUNDIT', v: s.packetAt ? Air.fmtTime(s.packetAt) : '-', sub: s.packetAt ? Air.fmtDate(s.packetAt) : 'asnjë' },
      { k: 'KOHA NGA MATJA', v: s.ageMs == null ? '-' : Air.fmtAge(s.ageMs) },
      { k: 'PLOTËSIA', v: Math.round(s.quality * 100) + '%' }
    ] })
    B.push({ type: 'head', text: 'MATJET AKTUALE' })
    B.push({ type: 'rows', items: Air.config.params.filter(p => node.sensors.indexOf(p.key) >= 0).map(p => {
      const v = s.usable ? s.values[p.key] : null; const bad = s.invalid[p.key]
      const lk = s.lastKnown ? s.lastKnown[p.key] : null
      if (v != null && !bad) return { k: p.label + ' (' + p.unit + ')', v: Air.fmtVal(p, v), color: Air.grade(p, v).fg }
      if (bad) return { k: p.label, v: 'e pavlefshme - ' + bad, color: '#9A5B00' }
      if (lk) return { k: p.label, v: 'e fundit ' + Air.fmtVal(p, lk.v) + ' ' + p.unit + ' (' + Air.fmtDate(lk.t) + ')', color: 'var(--text-tertiary)' }
      return { k: p.label, v: 'pa vlerë', color: 'var(--text-tertiary)' }
    }) })
    const nulls = meta.nulls || {}; const valid = meta.valid || {}
    B.push({ type: 'head', text: 'CILËSIA HISTORIKE E TË DHËNAVE' })
    B.push({ type: 'rows', items: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv'].filter(k => node.sensors.indexOf(k) >= 0).map(k => {
      const p = Air.paramByKey(k); const tot = (nulls[k] || 0) + (valid[k] || 0)
      const pct = tot ? (nulls[k] || 0) / tot * 100 : 0
      return { k: p.label + ' - vlera null', v: (nulls[k] || 0).toLocaleString('de-DE') + ' / ' + tot.toLocaleString('de-DE') + ' (' + pct.toFixed(1) + '%)', color: pct > 3 ? '#9A5B00' : '' }
    }) })
    if (node.notes) B.push({ type: 'note', text: node.notes })
    B.push({ type: 'actions', items: [
      { label: 'Konfiguro nyjen', variant: 'accent', icon: 'solar:tuning-2-linear', go: () => { state.dtab = 'config'; state.buf = Air.clone(node) } }
    ] })
  }
  if (tab === 'charts') {
    const mode = state.dmode || 'day'
    Air.nodeParams(node).forEach(p => B.push(lineBlock([node], p.key, mode)))
    B.push({ type: 'note', text: 'Periudha (dita / java / muaji) zgjidhet nga shiriti i filtrave sipër. Boshllëqet në vijë janë orë ose ditë pa asnjë matje të vlefshme.' })
  }
  if (tab === 'packets') {
    const pk = Air.source().packets(node)
    const pkFrom = pk.length ? String(pk[pk.length - 1][10]).slice(0, 16) : '-'
    const pkTo = pk.length ? String(pk[0][10]).slice(0, 16) : '-'
    B.push({ type: 'head', text: 'PAKETAT E FUNDIT TË REGJISTRUARA · ' + pkFrom + ' → ' + pkTo })
    B.push({ type: 'packets', items: pk.slice(0, 14).map(r => ({
      ts: String(r[10]).slice(5, 16), pm25: r[4] == null ? '·' : r[4], pm10: r[3] == null ? '·' : r[3],
      tmp: r[8] == null ? '·' : r[8], hum: r[2] == null ? '·' : r[2], snd: r[7] == null ? '·' : r[7], uv: r[9] == null ? '·' : r[9],
      c25: r[4] == null, c10: r[3] == null
    })) })
    B.push({ type: 'rows', items: [
      { k: 'Paketa gjithsej', v: (meta.n || 0).toLocaleString('de-DE') },
      { k: 'Intervali mesatar i matur', v: (meta.avgIntervalS || 0) + ' s' },
      { k: 'Ndërprerje mbi 1 orë', v: (meta.gaps1h || 0) + ' · më e gjata ' + (meta.maxGapH || 0) + ' orë' },
      { k: 'Rilidhje (DevAddr të ndryshme)', v: meta.rejoins || 1 },
      { k: 'DevAddr i fundit', v: meta.lastAdr || '-' },
      { k: 'E para / e fundit', v: (meta.first || '-') + ' → ' + (meta.last || '-') }
    ] })
    B.push({ type: 'note', text: 'Këto janë paketat e papërpunuara nga fundi i serisë së kësaj nyje, jo nga pozicioni aktual i replay-t. RSSI, SNR, bateria dhe gateway nuk ekzistojnë në eksportin aktual - kolonat përkatëse shfaqen automatikisht kur backend-i t\'i japë.' })
  }
  if (tab === 'config') {
    B.push({ type: 'fields', items: [
      field('id', 'ID e brendshme'), field('eui', 'Device EUI'),
      field('joinEui', 'Join EUI'), field('apiId', 'Identifikuesi i API-t'),
      field('name', 'Emri publik', { span2: true }),
      field('city', 'Qyteti', { kind: 'select', options: opts([['Tiranë', 'Tiranë'], ['Elbasan', 'Elbasan'], ['Korçë', 'Korçë']]) }),
      field('place', 'Place (dataset)'),
      field('address', 'Adresa', { span2: true }),
      field('lat', 'Gjerësia gjeografike', { kind: 'number', hint: 'Nuk vjen nga dataset-i - konfigurohet manualisht.' }),
      field('lng', 'Gjatësia gjeografike', { kind: 'number' }),
      field('installedAt', 'Data e instalimit', { kind: 'date' }),
      field('intervalS', 'Intervali i pritshëm (s)', { kind: 'number', hint: 'Statuset online/vonesë/offline llogariten mbi këtë vlerë.' }),
      field('tech', 'Teknologjia', { kind: 'select', options: opts([['lorawan', 'LoRaWAN'], ['rpi_api', 'Raspberry Pi - API']]), hint: 'Përcakton se si mbërrijnë paketat.' }),
      field('coverageM', 'Rrezja e mbulimit (m)', { kind: 'number', hint: 'Zona që ngjyroset në hartë. Zakonisht 100–200 m.' }),
      field('webhook', 'Webhook / endpoint i pranimit', { span2: true, hint: 'URL-ja ku kjo nyje dërgon paketat e saj.' }),
      field('transport', 'Transporti', { kind: 'select', options: opts([['LoRaWAN', 'LoRaWAN'], ['Wi-Fi / HTTP', 'Wi-Fi / HTTP']]) }),
      field('tz', 'Zona kohore'),
      toggleField('active', 'Aktive', 'Nyjet joaktive nuk llogariten në statuset e rrjetit.'),
      toggleField('public', 'E dukshme publikisht'),
      toggleField('maintenance', 'Në mirëmbajtje'),
      field('hw', 'Pajisja'),
      field('notes', 'Shënime', { kind: 'area', span2: true })
    ] })
    B.push({ type: 'head', text: 'PARAMETRAT E KËSAJ NYJEJE' })
    B.push(paramCfgBlock())
    B.push({ type: 'note', text: 'Çdo nyje mban vetëm parametrat e ndezur këtu - një nyje mund të ketë një sensor më shumë se një tjetër. Ngjyra e parë është ajo e parazgjedhur e parametrit; një ngjyrë tjetër vlen vetëm për këtë nyje.' })
  }
  return B
}

/* ---------- param drawer blocks ---------- */
function paramBlocks () {
  return [
    { type: 'fields', items: [
      field('key', 'Çelësi i brendshëm', { hint: 'Duhet të përputhet me fushën e burimit.' }),
      field('label', 'Etiketa publike'),
      field('long', 'Emri i plotë', { span2: true }),
      field('unit', 'Njësia'), field('dec', 'Shifra dhjetore', { kind: 'number' }),
      field('icon', 'Ikona (Iconify)'),
      field('physMin', 'Minimumi fizik i vlefshëm', { kind: 'number' }),
      field('physMax', 'Maksimumi fizik i vlefshëm', { kind: 'number', hint: 'Vlerat jashtë kësaj hapësire shënohen si të pavlefshme.' }),
      field('dispMin', 'Minimumi i shfaqjes', { kind: 'number' }),
      field('dispMax', 'Maksimumi i shfaqjes', { kind: 'number', hint: 'Përcakton shkallën e ngjyrave - e njëjta ngjyrë do të thotë gjithmonë e njëjta vlerë.' }),
      field('normal', 'Pragu normal', { kind: 'number' }),
      field('warn', 'Pragu i kujdesit', { kind: 'number' }),
      field('crit', 'Pragu kritik', { kind: 'number' }),
      field('lowWarn', 'Pragu i ulët', { kind: 'number' }),
      field('radiusM', 'Rrezja e heatmap-it (m)', { kind: 'number' }),
      field('blur', 'Zbutja (0–1)', { kind: 'number' }),
      field('opacity', 'Tejdukshmëria (0–1)', { kind: 'number' }),
      field('missing', 'Trajtimi i vlerave null', { kind: 'select', options: opts([['skip', 'Përjashto nga interpolimi'], ['last', 'Përdor vlerën e fundit të vlefshme'], ['zero', 'Trajto si zero']]) }),
      toggleField('public', 'E dukshme publikisht'),
      field('desc', 'Përshkrimi publik', { kind: 'area', span2: true }),
      field('note', 'Shënim në legjendë', { kind: 'area', span2: true })
    ] },
    { type: 'note', text: 'Portali publik lexon pikërisht këto vlera: legjenda, shkalla e ngjyrave, pragjet dhe teksti shpjegues nuk dublikohen askund tjetër.' }
  ]
}

/* ---------- the assembled drawer view ---------- */
const view = computed(() => {
  tick.value; state.rev
  const s = snap.value
  const d = state.drawer
  if (!d || !s) return { title: '', sub: '', tabs: [], blocks: [], footer: false }
  if (d.kind === 'node') {
    const known = Air.nodeById(d.id)
    const n = known || (state.buf && state.buf.id === d.id ? state.buf : null)
    if (!n) return { title: '', sub: '', tabs: [], blocks: [], footer: false }
    const tabs = (known
      ? [['overview', 'Përmbledhje'], ['charts', 'Grafikët'], ['packets', 'Paketat'], ['config', 'Konfigurimi']]
      : [['config', 'Konfigurimi']]).map(([value, label]) => ({ value, label }))
    const blocks = known ? nodeBlocks(known) : nodeBlocks(Object.assign({ sensors: [], scale: {} }, n))
    return {
      title: n.name,
      sub: n.id + ' · ' + n.city + ' · ' + n.transport + (known ? ' · ' + Air.STATUS[s.byId[n.id].status].label : ' · e re'),
      tabs, blocks,
      footer: (state.dtab || 'overview') === 'config' ? 'Ruaj nyjen' : false
    }
  }
  if (d.kind === 'param') {
    return { title: (state.buf && state.buf.label) || 'Parametri', sub: 'Pragjet, shkalla e ngjyrave dhe kalibrimi', tabs: [], blocks: paramBlocks(), footer: 'Ruaj parametrin' }
  }
  return { title: '', sub: '', tabs: [], blocks: [], footer: false }
})

function setDtab (k) {
  state.dtab = k
  if (k === 'config' && state.drawer) state.buf = Air.clone(Air.nodeById(state.drawer.id) || state.buf)
}

function saveDrawer () {
  const d = state.drawer; const buf = state.buf
  if (!d || !buf) return
  const num = (v, dflt) => { const n = parseFloat(v); return isFinite(n) ? n : dflt }
  if (d.kind === 'node') {
    const existing = Air.nodeById(d.id)
    const n = existing || {}
    Object.assign(n, buf, {
      lat: num(buf.lat, n.lat), lng: num(buf.lng, n.lng),
      intervalS: Math.max(10, num(buf.intervalS, n.intervalS || 300)),
      coverageM: Math.max(20, num(buf.coverageM, n.coverageM || 150))
    })
    if (!existing) Air.config.nodes.push(n)
    Air.persist(); store.toast('Nyja ' + n.id + ' u ruajt')
  } else if (d.kind === 'param') {
    const p = Air.paramByKey(d.id)
    if (p) {
      ['dec', 'physMin', 'physMax', 'dispMin', 'dispMax', 'normal', 'warn', 'crit', 'lowWarn', 'radiusM', 'blur', 'opacity']
        .forEach(k => { buf[k] = (buf[k] === '' || buf[k] == null) ? null : num(buf[k], p[k]) })
      Object.assign(p, buf)
      Air.persist(); store.toast('Parametri ' + p.label + ' u ruajt')
    }
  }
  store.closeDrawer()
  store.refreshSnap()
}
</script>

<style scoped>
.adm-textarea {
  width: 100%;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-card);
  padding: 8px 11px;
  font-size: 13px;
  font-family: var(--font-body);
  color: var(--text-primary);
  resize: vertical;
  line-height: var(--lh-base);
}
.adm-textarea:focus-visible { outline: 2px solid var(--teal-400); outline-offset: 1px; }
</style>
