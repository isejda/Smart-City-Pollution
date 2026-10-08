/* ==========================================================================
   chart.js - framework-agnostic SVG chart builders, ported verbatim from the
   original Portali Publik page. Both `chartSVG` and `spark` return an SVG
   string that the Vue components render via v-html. All colour / format work
   is delegated to the shared window.Air engine, exactly like the original.
   ========================================================================== */
const A = window.Air

export function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
  })
}

export function chartSVG(o) {
  var pts = o.points || [], p = o.param, W = o.w || 820, H = o.h || 250
  var padL = 42, padR = 14, padT = 16, padB = 28
  var iw = W - padL - padR, ih = H - padT - padB
  var vals = pts.filter(function (d) { return d.v != null }).map(function (d) { return d.v })
  var fc = o.forecast || []
  fc.forEach(function (d) { vals.push(d.hi); vals.push(d.lo) })
  if (!vals.length) return '<div style="height:' + H + 'px;display:flex;align-items:center;justify-content:center;color:var(--text-tertiary);font-size:13px">' + esc(A.t('no_data')) + '</div>'
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals)
  var padv = (hi - lo) * 0.18 || Math.max(1, Math.abs(hi) * 0.1); lo -= padv; hi += padv
  if (p.key !== 'tmp') lo = Math.max(lo, Math.min(0, p.physMin))
  var span = (hi - lo) || 1
  var total = pts.length + fc.length
  var X = function (i) { return padL + (total < 2 ? iw / 2 : i * iw / (total - 1)) }
  var Y = function (v) { return padT + ih - (v - lo) / span * ih }
  var col = A.paramColor(p, o.node)
  var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto;display:block;overflow:visible" role="img">'
  s += '<defs><linearGradient id="g' + o.id + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + col + '" stop-opacity=".26"/><stop offset="1" stop-color="' + col + '" stop-opacity="0"/></linearGradient></defs>'
  for (var g = 0; g <= 4; g++) {
    var gv = lo + span * g / 4, gy = Y(gv)
    s += '<line x1="' + padL + '" y1="' + gy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + gy.toFixed(1) + '" stroke="' + (g === 0 ? '#D8D8D8' : '#EEEEEE') + '" stroke-width="1"/>'
    s += '<text x="' + (padL - 7) + '" y="' + (gy + 3.5).toFixed(1) + '" text-anchor="end" font-size="10" fill="#979797" font-family="var(--font-body)">' + A.fmtVal(p, gv) + '</text>'
  }
  /* observed */
  var seg = [], segs = []
  pts.forEach(function (d, i) { if (d.v == null) { if (seg.length > 1) segs.push(seg); seg = [] } else seg.push([X(i), Y(d.v)]) })
  if (seg.length > 1) segs.push(seg)
  segs.forEach(function (sg) {
    var d0 = 'M' + sg.map(function (q) { return q[0].toFixed(1) + ',' + q[1].toFixed(1) }).join('L')
    s += '<path d="' + d0 + 'L' + sg[sg.length - 1][0].toFixed(1) + ',' + (padT + ih) + 'L' + sg[0][0].toFixed(1) + ',' + (padT + ih) + 'Z" fill="url(#g' + o.id + ')"/>'
    s += '<path d="' + d0 + '" fill="none" stroke="' + col + '" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>'
  })
  if (o.dots !== false && pts.length <= 31) {
    pts.forEach(function (d, i) {
      if (d.v == null) return
      s += '<circle cx="' + X(i).toFixed(1) + '" cy="' + Y(d.v).toFixed(1) + '" r="3" fill="#fff" stroke="' + col + '" stroke-width="2"><title>' + esc(d.full || d.label) + ' - ' + A.fmtVal(p, d.v) + ' ' + esc(A.tp(p, 'unit')) + '</title></circle>'
    })
  }
  /* forecast */
  if (fc.length) {
    var off = pts.length
    var up = fc.map(function (d, i) { return X(off + i).toFixed(1) + ',' + Y(d.hi).toFixed(1) })
    var dn = fc.map(function (d, i) { return X(off + i).toFixed(1) + ',' + Y(d.lo).toFixed(1) }).reverse()
    s += '<polygon points="' + up.concat(dn).join(' ') + '" fill="' + col + '" opacity=".13"/>'
    var last = pts.filter(function (d) { return d.v != null }).slice(-1)[0]
    var fp = (last ? ('M' + X(pts.indexOf(last)).toFixed(1) + ',' + Y(last.v).toFixed(1) + 'L') : 'M') + fc.map(function (d, i) { return X(off + i).toFixed(1) + ',' + Y(d.v).toFixed(1) }).join('L')
    s += '<path d="' + fp + '" fill="none" stroke="' + col + '" stroke-width="2" stroke-dasharray="5 4" opacity=".85"/>'
    s += '<line x1="' + X(off - 0.5).toFixed(1) + '" y1="' + padT + '" x2="' + X(off - 0.5).toFixed(1) + '" y2="' + (padT + ih) + '" stroke="#AFAFAF" stroke-width="1" stroke-dasharray="3 3"/>'
  }
  /* x labels */
  var all = pts.concat(fc.map(function (d) { return { label: A.fmtTime(d.t), t: d.t } }))
  var every = Math.max(1, Math.ceil(all.length / (W > 600 ? 8 : 5)))
  all.forEach(function (d, i) {
    if (i % every) return
    s += '<text x="' + X(i).toFixed(1) + '" y="' + (H - 9) + '" text-anchor="middle" font-size="10" fill="#979797" font-family="var(--font-body)">' + esc(d.label) + '</text>'
  })
  return s + '</svg>'
}

export function spark(pts, p, node, w, h) {
  var vals = pts.filter(function (d) { return d.v != null }).map(function (d) { return d.v })
  if (vals.length < 2) return '<div style="height:' + h + 'px"></div>'
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), sp = (hi - lo) || 1
  var col = A.paramColor(p, node)
  var d0 = pts.map(function (d, i) {
    if (d.v == null) return null
    return (i * w / (pts.length - 1)).toFixed(1) + ',' + (h - 2 - (d.v - lo) / sp * (h - 6)).toFixed(1)
  }).filter(Boolean)
  return '<svg viewBox="0 0 ' + w + ' ' + h + '" style="width:100%;height:' + h + 'px;display:block"><path d="M' + d0.join('L') + '" fill="none" stroke="' + col + '" stroke-width="2" stroke-linejoin="round"/></svg>'
}
