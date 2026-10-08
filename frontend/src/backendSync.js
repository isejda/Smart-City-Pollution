/*
 * Server-driven console: mirror operator config edits back to the Django
 * backend. Every edit in the monitoring console (replay settings, status
 * thresholds, data source) already funnels through `Air.persist()`, so we
 * wrap it once and PATCH the changed rows to the API. Only the settings
 * endpoint is writable server-side; node/parameter edits stay local (their
 * API is read-only). No-op unless the app is connected to the backend, so
 * offline/bundled mode is unaffected.
 */
function mapSettings(s) {
  return {
    tz: s.tz,
    online_mult: s.onlineMult,
    delayed_mult: s.delayedMult,
    validity_min: s.validityMin,
    source: s.source,
    rest_base: s.restBase,
    ws_url: s.wsUrl,
    poll_s: s.pollS,
    replay: !!s.replay,
    replay_speed: s.replaySpeed
  }
}

export function initBackendSync(root) {
  const scope = root || (typeof window !== 'undefined' ? window : globalThis)
  const Air = scope.Air
  const base = scope.__AIR_SOURCE__ === 'backend' ? (scope.__AIR_API__ || '') : ''
  if (!Air || !base || Air.__backendSync) return
  Air.__backendSync = true

  const patch = (path, body) => {
    const headers = { 'Content-Type': 'application/json' }
    const token = scope.localStorage && scope.localStorage.getItem('access_token')
    if (token) headers.Authorization = 'Bearer ' + token
    return fetch(base + path, { method: 'PATCH', headers, body: JSON.stringify(body) })
      .catch((e) => console.warn('[air] backend sync failed', path, e && e.message))
  }

  let lastSettings = JSON.stringify(mapSettings(Air.config.settings))

  let timer = null
  const flush = () => {
    const cur = mapSettings(Air.config.settings)
    const curStr = JSON.stringify(cur)
    if (curStr !== lastSettings) {
      lastSettings = curStr
      patch('/api/settings/', cur)
    }
  }

  const orig = Air.persist
  Air.persist = function wrappedPersist() {
    const out = orig.apply(this, arguments)
    clearTimeout(timer)
    timer = setTimeout(flush, 400) // debounce bursts of edits
    return out
  }
  console.info('[air] server-driven console enabled →', base)
}

export default initBackendSync
