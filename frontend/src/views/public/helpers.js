/* ==========================================================================
   helpers.js - small formatting utilities shared by the public-portal
   components, ported from the original page's inline helpers.
   ========================================================================== */
const A = window.Air

export function num(n) {
  n = Math.round(n || 0)
  return A.lang === 'en'
    ? n.toLocaleString('en-US')
    : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

function replaceAll(s, a, b) { return s.split(a).join(b) }

export function fill(s) {
  var st = A.networkStats()
  return replaceAll(replaceAll(s, '{rows}', num(st.rows)), '{nodes}', String(st.nodes))
}

export function excerpt(s, max) {
  if (s.length <= max) return s
  var c = s.slice(0, max)
  return c.slice(0, c.lastIndexOf(' ')) + '…'
}

export function pad2(n) { return n < 10 ? '0' + n : '' + n }
