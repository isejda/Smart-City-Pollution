/* ==========================================================================
   Smart City Pollution - synthetic replay dataset (window.AIR_DATASET)
   --------------------------------------------------------------------------
   The design bundle shipped `air-dataset.js` EMPTY, so the shared engine
   (air-core.js) had nothing to replay. This module rebuilds a dataset in the
   exact shape air-core.js consumes, so the maps, charts, KPIs and forecasts
   all populate with plausible, deterministic data.

   Shape per node (keyed by node EUI):
     { h0Ms, hours{field:[raw|null]}, daily{field:[mean|null]}, days[],
       diurnal{field:[24]}, tail[{t,field:val}], n, first, last,
       avgIntervalS, rejoins, gaps1h, maxGapH, nulls{field:N}, valid{field:N} }

   Values in `hours` are RAW sensor values - air-core.js calibrate() converts
   snd/uv/rain raw -> % of the node's scale, and uses pm/tmp/hum/pres as-is.
   Everything is generated with a seeded PRNG so a given build is reproducible.
   Swap this module for a real backend adapter to go live.
   ========================================================================== */
(function (global) {
  'use strict'

  var HOUR = 3600e3
  var GLOBAL_FIRST = '2026-02-22 00:00:00'
  var GLOBAL_LAST = '2026-06-30 23:00:00'

  function parseTs(s) { return Date.parse(String(s).replace(' ', 'T') + 'Z') }
  function pad(n) { return n < 10 ? '0' + n : '' + n }
  function fmtWall(ms) {
    var d = new Date(ms)
    return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate()) +
      ' ' + pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()) + ':' + pad(d.getUTCSeconds())
  }
  function dayKey(ms) {
    var d = new Date(ms)
    return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate())
  }

  // deterministic PRNG (mulberry32) seeded from a string
  function seed(str) {
    var h = 1779033703 ^ str.length
    for (var i = 0; i < str.length; i++) {
      h = Math.imul(h ^ str.charCodeAt(i), 3432918353)
      h = (h << 13) | (h >>> 19)
    }
    var a = h >>> 0
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0
      var t = Math.imul(a ^ (a >>> 15), 1 | a)
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
  }

  var h0 = parseTs(GLOBAL_FIRST)
  var hEnd = parseTs(GLOBAL_LAST)
  var TOTAL = Math.round((hEnd - h0) / HOUR) + 1

  // ---- node profiles ------------------------------------------------------
  // start/end = active reporting window (wall-clock). Outside it -> null.
  // base values drive the mean of each field; a few carry the real dataset's
  // documented quirks (sensor faults, sentinel values, saturation).
  var NODES = [
    { eui: 'A8404172C75D105A', scale: 1023, start: '2026-02-22 00:00:00', end: GLOBAL_LAST,
      intervalS: 100, fields: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
      pm: 18, presBase: 1013, nullPm: 0.047 },
    { eui: 'A84041DA335D105B', scale: 1023, start: '2026-03-01 00:00:00', end: GLOBAL_LAST,
      intervalS: 150, fields: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
      pm: 21, presBase: 1013, uvStuck: true },
    { eui: 'raspberrypi_korce_1', scale: 255, start: '2026-04-24 00:00:00', end: GLOBAL_LAST,
      intervalS: 102, fields: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain', 'pres'],
      pm: 14, presBase: 920, tmpSentinel: 0.01 },
    { eui: 'raspberrypi_Korca_Universiteti', scale: 255, start: '2026-04-23 00:00:00', end: GLOBAL_LAST,
      intervalS: 180, fields: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain', 'pres'],
      pm: 12, presBase: 920 },
    { eui: 'raspberrypi_elb_nyja2', scale: 255, start: '2026-04-10 00:00:00', end: GLOBAL_LAST,
      intervalS: 805, fields: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
      pm: 0.36, humLow: 11, presBase: 1010 },
    { eui: 'raspberrypi_elb_universiteti', scale: 255, start: '2026-04-10 00:00:00', end: GLOBAL_LAST,
      intervalS: 362, fields: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
      pm: 13, presBase: 1010 }
  ]

  // seasonal factor: late winter (Feb) higher PM & cold, summer (Jun) lower PM & warm.
  // progress 0 at GLOBAL_FIRST -> 1 at GLOBAL_LAST.
  function season(ms) { return (ms - h0) / (hEnd - h0) }

  function buildNode(cfg) {
    var start = parseTs(cfg.start), end = parseTs(cfg.end)
    var rnd = {}
    cfg.fields.forEach(function (f) { rnd[f] = seed(cfg.eui + '|' + f) })

    var hours = {}, nulls = {}, valid = {}
    cfg.fields.forEach(function (f) { hours[f] = new Array(TOTAL).fill(null); nulls[f] = 0; valid[f] = 0 })

    var gaps1h = 0, maxGap = 0, curGap = 0, rejoins = 0, wasNull = true

    for (var i = 0; i < TOTAL; i++) {
      var t = h0 + i * HOUR
      var inWindow = t >= start && t <= end
      var d = new Date(t)
      var hod = d.getUTCHours()
      var prog = season(t)

      // simple gap: whole node silent for a stretch (comms drop) ~ rare
      var silent = !inWindow
      if (inWindow && rnd.tmp() < 0.006) silent = true // occasional short outage

      if (silent) {
        gaps1h++; curGap++; if (curGap > maxGap) maxGap = curGap
        wasNull = true
        continue
      }
      if (wasNull && inWindow) { rejoins++; }
      wasNull = false
      curGap = 0

      cfg.fields.forEach(function (f) {
        var r = rnd[f]
        var v = null
        if (f === 'pm25') {
          var diur = 1 + 0.45 * bell(hod, 8, 3) + 0.55 * bell(hod, 20, 3) // rush peaks
          var seas = 1 - 0.45 * prog // cleaner into summer
          v = cfg.pm * diur * seas * (0.75 + r() * 0.5)
          if (r() < 0.02) v += 20 + r() * 30 // local burning spike
          v = clamp(v, 0.1, 90)
          if (cfg.nullPm && r() < cfg.nullPm) v = null
        } else if (f === 'pm10') {
          var base10 = (cfg.pm * 1.7 + 6) * (1 - 0.4 * prog)
          v = base10 * (0.7 + r() * 0.6) + 4
          if (cfg.pm10Spike && r() < 0.004) v = 1000 + r() * 900 // invalid out-of-range
          v = clamp(v, 1, 2000)
        } else if (f === 'tmp') {
          var seasonT = 7 + 18 * prog // ~7C Feb -> ~25C Jun
          var diurT = -5 * Math.cos((hod - 3) / 24 * 2 * Math.PI)
          v = seasonT + diurT + (r() - 0.5) * 3
          v = clamp(v, -3, 44)
          if (cfg.tmpSentinel && r() < cfg.tmpSentinel) v = 0 // failed-sensor sentinel
        } else if (f === 'hum') {
          if (cfg.humLow != null) {
            v = cfg.humLow + (r() - 0.5) * 6 // damaged sensor stuck low
          } else {
            var baseH = 62 - 22 * (bell(hod, 15, 5)) // drier midday
            v = baseH + (r() - 0.5) * 14 - 8 * prog
          }
          v = clamp(v, 3, 98)
        } else if (f === 'snd') {
          var diurS = 0.32 + 0.22 * bell(hod, 9, 4) + 0.2 * bell(hod, 19, 4) - 0.12 * bell(hod, 3, 3)
          v = cfg.scale * diurS * (0.8 + r() * 0.4)
          v = clamp(v, 0, cfg.scale)
        } else if (f === 'uv') {
          if (cfg.uvStuck) {
            v = cfg.scale * 0.975 + (r() - 0.5) * 8 // saturated sensor
          } else {
            var day = bell(hod, 13, 3.2) // daytime bell
            v = cfg.scale * (0.05 + 0.85 * day * (0.8 + 0.4 * prog)) * (0.85 + r() * 0.3)
          }
          v = clamp(v, 0, cfg.scale)
        } else if (f === 'pres') {
          v = cfg.presBase + Math.sin(i / 40) * 6 + (r() - 0.5) * 4
          v = clamp(v, 850, 1080)
        } else if (f === 'rain') {
          v = r() < 0.15 ? r() * cfg.scale * 0.6 : r() * cfg.scale * 0.05
          v = clamp(v, 0, cfg.scale)
        }

        // sparse per-field dropouts
        if (v != null && r() < 0.012) v = null

        if (v == null) { nulls[f]++ }
        else { valid[f]++; hours[f][i] = Math.round(v * 1000) / 1000 }
      })
    }

    // ---- daily means + day list -----------------------------------------
    var days = [], daily = {}
    cfg.fields.forEach(function (f) { daily[f] = [] })
    var dayIdx = {}
    for (var j = 0; j < TOTAL; j++) {
      var key = dayKey(h0 + j * HOUR)
      if (dayIdx[key] == null) { dayIdx[key] = days.length; days.push(key) }
    }
    cfg.fields.forEach(function (f) {
      var sums = new Array(days.length).fill(0), cnts = new Array(days.length).fill(0)
      for (var k = 0; k < TOTAL; k++) {
        var vv = hours[f][k]
        if (vv == null) continue
        var di = dayIdx[dayKey(h0 + k * HOUR)]
        sums[di] += vv; cnts[di]++
      }
      daily[f] = sums.map(function (s, i2) { return cnts[i2] ? Math.round(s / cnts[i2] * 1000) / 1000 : null })
    })

    // ---- diurnal profile (mean by hour-of-day) --------------------------
    var diurnal = {}
    cfg.fields.forEach(function (f) {
      var s = new Array(24).fill(0), c = new Array(24).fill(0)
      for (var m = 0; m < TOTAL; m++) {
        var vv = hours[f][m]
        if (vv == null) continue
        var hh = new Date(h0 + m * HOUR).getUTCHours()
        s[hh] += vv; c[hh]++
      }
      diurnal[f] = s.map(function (x, i3) { return c[i3] ? Math.round(x / c[i3] * 1000) / 1000 : null })
    })

    // ---- tail: last ~48 hourly packets ----------------------------------
    var tail = []
    var endIdx = Math.min(TOTAL - 1, Math.round((Math.min(end, hEnd) - h0) / HOUR))
    for (var q = Math.max(0, endIdx - 47); q <= endIdx; q++) {
      var rec = { t: h0 + q * HOUR }
      var any = false
      cfg.fields.forEach(function (f) { if (hours[f][q] != null) { rec[f] = hours[f][q]; any = true } })
      if (any) tail.push(rec)
    }

    // ---- meta ------------------------------------------------------------
    var winStart = fmtWall(Math.max(start, h0))
    var winEnd = fmtWall(Math.min(end, hEnd))
    var spanS = (Math.min(end, hEnd) - Math.max(start, h0)) / 1000
    var expected = Math.round(spanS / cfg.intervalS)
    var n = Math.round(expected * (0.9 + (seed(cfg.eui)() * 0.08)))

    return {
      h0Ms: h0, hours: hours, daily: daily, days: days, diurnal: diurnal, tail: tail,
      n: n, first: winStart, last: winEnd,
      avgIntervalS: cfg.intervalS, rejoins: rejoins, gaps1h: gaps1h, maxGapH: maxGap,
      nulls: nulls, valid: valid
    }
  }

  // gaussian-ish bell centred at c with width w, evaluated on the 24h clock
  function bell(hod, c, w) {
    var dx = Math.min(Math.abs(hod - c), 24 - Math.abs(hod - c))
    return Math.exp(-(dx * dx) / (2 * w * w))
  }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v }

  var nodes = {}, totalRows = 0
  NODES.forEach(function (cfg) {
    var s = buildNode(cfg)
    nodes[cfg.eui] = s
    totalRows += s.n
  })

  global.AIR_DATASET = {
    source: 'Dataset sintetik (replay demonstrimi)',
    rows: totalRows,
    first: GLOBAL_FIRST,
    last: GLOBAL_LAST,
    nodes: nodes
  }
})(window)
