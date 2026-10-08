import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// ---- global styles -------------------------------------------------------
import 'leaflet/dist/leaflet.css'
import './styles/base.css'

/*
 * Boot sequence
 * -------------
 * The Air engine reads `window.AIR_DATASET` at import time, so the dataset must
 * be in place BEFORE air-core.js loads. We first try to hydrate it from the
 * Django backend (`GET /api/dataset/`); if the API is unreachable we fall back
 * to the bundled synthetic dataset, so the app always works offline. Only then
 * do we load the engine and mount the app.
 */
const DEFAULT_API = 'http://localhost:8000'
// Set VITE_API_URL='' to force bundled data, or to your API origin to connect.
const API = (import.meta.env.VITE_API_URL ?? DEFAULT_API).replace(/\/$/, '')

async function loadDataset() {
  if (API) {
    try {
      const ctrl = new AbortController()
      const timer = setTimeout(() => ctrl.abort(), 8000)
      const res = await fetch(API + '/api/dataset/', {
        headers: { Accept: 'application/json' },
        signal: ctrl.signal,
      })
      clearTimeout(timer)
      if (res.ok) {
        window.AIR_DATASET = await res.json()
        window.__AIR_SOURCE__ = 'backend'
        window.__AIR_API__ = API
        console.info('[air] hydrated from backend', API)
        return
      }
      console.warn('[air] backend responded', res.status, '- using bundled dataset')
    } catch (e) {
      console.warn('[air] backend unreachable - using bundled dataset:', e.message)
    }
  }
  await import('./engine/air-dataset.js') // sets window.AIR_DATASET
  window.__AIR_SOURCE__ = 'bundled'
}

async function boot() {
  await loadDataset()
  // engine attaches to window.Air; order matters (core reads the dataset, extra patches it)
  await import('./engine/air-core.js')
  await import('./engine/air-extra.js')
  // when connected to the backend, mirror operator config edits back to it
  const { initBackendSync } = await import('./backendSync.js')
  initBackendSync(window)

  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.mount('#app')
}

boot()
