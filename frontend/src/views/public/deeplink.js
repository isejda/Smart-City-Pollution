/* ==========================================================================
   deeplink - pure helpers that translate between the Public Portal's shared
   `ui` state (+ the active language) and the hash-route query string, so a
   view can be shared/restored via URL (e.g. #/?city=Korçë&param=no2&node=ND-04).

   Everything here is framework-agnostic and side-effect free; PublicPortal.vue
   owns the vue-router wiring. Defaults are omitted from the query so plain
   URLs stay clean, and every reader is guarded so a bad param never throws.
   ========================================================================== */

// Managed query keys and the state values that are treated as "default" (and
// therefore left out of the URL entirely).
export const MANAGED_KEYS = ['city', 'param', 'node', 'lang']
export const DEFAULTS = { city: 'Tiranë', param: 'pm25', lang: 'sq' }
const CITIES = ['Tiranë', 'Korçë', 'Elbasan']

// vue-router query values are string | string[] | null; normalise to a string.
function str(v) {
  if (typeof v === 'string') return v
  if (Array.isArray(v) && typeof v[0] === 'string') return v[0]
  return null
}

export function isValidCity(c) { return c === '*' || CITIES.indexOf(c) >= 0 }

export function isValidParam(Air, k) {
  try { return !!(Air && Air.publicParams().some(function (p) { return p.key === k })) } catch (e) { return false }
}

// Returns the node object if `id` is a known, public node - else null.
export function nodeIfValid(Air, id) {
  try { var n = Air && Air.nodeById(id); return n && n.public ? n : null } catch (e) { return null }
}

function setOrDel(q, k, v) { if (v == null || v === '') delete q[k]; else q[k] = v }

// Merge the managed keys derived from `state` into a copy of `current`, so any
// unrelated query keys already present are preserved untouched.
export function buildQuery(current, state) {
  var q = Object.assign({}, current || {})
  setOrDel(q, 'city', state.city && state.city !== DEFAULTS.city ? state.city : null)
  setOrDel(q, 'param', state.param && state.param !== DEFAULTS.param ? state.param : null)
  setOrDel(q, 'node', state.node || null)
  setOrDel(q, 'lang', state.lang === 'en' ? 'en' : null)
  return q
}

// Read a route query into a validated patch. Unknown/invalid values are simply
// dropped. `node` (when valid) is returned as its id plus its city, so the
// caller can make sure the linked node is actually visible on the map.
export function parseQuery(Air, query) {
  var out = {}
  var q = query || {}
  var city = str(q.city); if (city && isValidCity(city)) out.city = city
  var param = str(q.param); if (param && isValidParam(Air, param)) out.param = param
  if (str(q.lang) === 'en') out.lang = 'en'
  var node = str(q.node); var n = node && nodeIfValid(Air, node)
  if (n) { out.node = n.id; out.nodeCity = n.city }
  return out
}

// True when two query objects agree on every managed key (treating
// missing/undefined as equal), so we can skip a no-op router.replace.
export function sameManaged(a, b) {
  a = a || {}; b = b || {}
  for (var i = 0; i < MANAGED_KEYS.length; i++) {
    var k = MANAGED_KEYS[i]
    var av = a[k] == null ? '' : a[k]
    var bv = b[k] == null ? '' : b[k]
    if (av !== bv) return false
  }
  return true
}
