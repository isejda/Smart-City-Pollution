/* ==========================================================================
   AirMonitor - shared core
   Data adapter · configuration store · status · forecast
   · IDW parameter-heatmap layer for Leaflet.
   Loaded by "Portali Publik.html" and "Portali Monitorimit.dc.html".
   Requires: air-dataset.js (window.AIR_DATASET). Leaflet only for Air.idwLayer().
   ========================================================================== */
(function (global) {
'use strict';

var DS = global.AIR_DATASET || { nodes: {} };
var HOUR = 3600e3, MIN = 60e3;

/* ---------------------------------------------------------------- time ----
   Dataset timestamps are naive Europe/Tirane wall-clock strings. We parse
   them as UTC so arithmetic is DST-free and formatting reproduces the exact
   wall time that was recorded. Everything user-facing is labelled Europe/Tirane. */
function parseTs(s) { return Date.parse(String(s).replace(' ', 'T') + 'Z'); }
function pad(n) { return n < 10 ? '0' + n : '' + n; }
function fmtTime(t) { var d = new Date(t); return pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()); }
var MONTHS = ['jan', 'shk', 'mar', 'pri', 'maj', 'qer', 'korr', 'gush', 'sht', 'tet', 'nën', 'dhj'];
var DAYS = ['e diel', 'e hënë', 'e martë', 'e mërkurë', 'e enjte', 'e premte', 'e shtunë'];
function fmtDate(t) { var d = new Date(t); return d.getUTCDate() + ' ' + MONTHS[d.getUTCMonth()]; }
function fmtDateTime(t) { return fmtDate(t) + ' ' + new Date(t).getUTCFullYear() + ', ' + fmtTime(t); }
function fmtDayName(t) { return DAYS[new Date(t).getUTCDay()]; }
function fmtAge(ms) {
  if (ms == null || !isFinite(ms)) return '-';
  var s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return s + ' sek';
  var m = Math.round(s / 60); if (m < 60) return m + ' min';
  var h = Math.floor(m / 60); if (h < 48) return h + ' orë' + (m % 60 ? ' ' + (m % 60) + ' min' : '');
  var d = Math.floor(h / 24); if (d < 60) return d + ' ditë';
  return Math.floor(d / 30) + ' muaj';
}

/* ----------------------------------------------------------- parameters ----
   Every threshold, range, gradient and conversion the UI uses lives here and
   is editable from the admin portal. Nothing is hardcoded in the views. */
var DEFAULT_PARAMS = [
  {
    key: 'pm25', field: 'pm25', label: 'PM2.5', long: 'Grimca të imëta PM2.5',
    unit: 'µg/m³', icon: 'mdi:blur', dec: 1, public: true,
    desc: 'Grimca nën 2.5 µm që depërtojnë thellë në mushkëri dhe kalojnë në gjak.',
    physMin: 0, physMax: 1000, dispMin: 0, dispMax: 60,
    normal: 15, warn: 25, crit: 50, lowWarn: null,
    gradient: [[0, '#1F8A4C'], [0.25, '#A9C23F'], [0.45, '#F2C230'], [0.65, '#E07E2E'], [0.85, '#B1322F'], [1, '#6D28D9']],
    radiusM: 4200, blur: 0.55, opacity: 0.72, missing: 'skip',
    note: 'Kufiri ditor i OBSH-së: 15 µg/m³.'
  },
  {
    key: 'pm10', field: 'pm10', label: 'PM10', long: 'Grimca të thëna PM10',
    unit: 'µg/m³', icon: 'mdi:blur-linear', dec: 1, public: true,
    desc: 'Pluhur nga trafiku, ndërtimet dhe djegia e druve.',
    physMin: 0, physMax: 2000, dispMin: 0, dispMax: 120,
    normal: 45, warn: 75, crit: 120, lowWarn: null,
    gradient: [[0, '#1F8A4C'], [0.25, '#A9C23F'], [0.45, '#F2C230'], [0.65, '#E07E2E'], [0.85, '#B1322F'], [1, '#6D28D9']],
    radiusM: 4200, blur: 0.55, opacity: 0.72, missing: 'skip',
    note: 'Kufiri ditor i OBSH-së: 45 µg/m³.'
  },
  {
    key: 'tmp', field: 'tmp', label: 'Temperatura', long: 'Temperatura e ajrit',
    unit: '°C', icon: 'mdi:thermometer', dec: 1, public: true,
    desc: 'Temperatura e ajrit e matur në lartësinë e nyjes.',
    physMin: -25, physMax: 60, dispMin: 0, dispMax: 42,
    normal: 30, warn: 35, crit: 40, lowWarn: 0,
    gradient: [[0, '#1E3A8A'], [0.2, '#38BDF8'], [0.4, '#34A853'], [0.6, '#F2C230'], [0.8, '#E07E2E'], [1, '#B1322F']],
    radiusM: 9000, blur: 0.7, opacity: 0.6, missing: 'skip',
    note: 'Vlera 0.0 raportohet nga disa nyje si shenjë e sensorit të pavlefshëm.'
  },
  {
    key: 'hum', field: 'hum', label: 'Lagështia', long: 'Lagështia relative',
    unit: '%', icon: 'mdi:water-percent', dec: 0, public: true,
    desc: 'Lagështia relative - ndikon te qëndrimi pezull i grimcave.',
    physMin: 0, physMax: 100, dispMin: 0, dispMax: 100,
    normal: 60, warn: 80, crit: 95, lowWarn: 20,
    gradient: [[0, '#C2843A'], [0.25, '#E3C77A'], [0.45, '#34A853'], [0.7, '#38BDF8'], [1, '#1E3A8A']],
    radiusM: 9000, blur: 0.7, opacity: 0.55, missing: 'skip',
    note: 'E thatë nën 30% · komfort 40–60% · e lartë mbi 70%.'
  },
  {
    key: 'snd', field: 'snd', label: 'Zhurma', long: 'Niveli i zhurmës (raw)',
    unit: '% e shkallës', icon: 'mdi:volume-high', dec: 0, public: true,
    desc: 'Sinjal i papërpunuar nga mikrofoni, i normalizuar në shkallën e sensorit. Nuk është dB - sensorët nuk janë kalibruar akustikisht.',
    physMin: 0, physMax: 100, dispMin: 0, dispMax: 100,
    normal: 35, warn: 55, crit: 75, lowWarn: null,
    gradient: [[0, '#1F8A4C'], [0.35, '#F2C230'], [0.65, '#E07E2E'], [1, '#B1322F']],
    radiusM: 2600, blur: 0.5, opacity: 0.7, missing: 'skip',
    note: 'Konvertim raw→% për nyje; asnjë formulë dB nuk është e validuar.'
  },
  {
    key: 'uv', field: 'uv', label: 'UV', long: 'Rrezatimi UV (raw)',
    unit: '% e shkallës', icon: 'mdi:weather-sunny', dec: 0, public: true,
    desc: 'Dalje e papërpunuar e fotodiodës UV, e normalizuar në shkallën e sensorit. Nuk është Indeksi UV - kërkon kalibrim.',
    physMin: 0, physMax: 100, dispMin: 0, dispMax: 100,
    normal: 40, warn: 60, crit: 80, lowWarn: null,
    gradient: [[0, '#1F8A4C'], [0.3, '#F2C230'], [0.55, '#E07E2E'], [0.8, '#B1322F'], [1, '#6D28D9']],
    radiusM: 12000, blur: 0.75, opacity: 0.6, missing: 'skip',
    note: 'Vlera ≥98% tregon sensor të ngopur ose të bllokuar.'
  },
  {
    key: 'pres', field: 'pres', label: 'Presioni', long: 'Presioni atmosferik',
    unit: 'hPa', icon: 'mdi:gauge', dec: 1, public: false,
    desc: 'Raportohet vetëm nga nyjet Raspberry Pi me sensor BMP.',
    physMin: 850, physMax: 1080, dispMin: 890, dispMax: 1020,
    normal: 1030, warn: 1050, crit: 1070, lowWarn: 900,
    gradient: [[0, '#38BDF8'], [0.5, '#34A853'], [1, '#E07E2E']],
    radiusM: 12000, blur: 0.8, opacity: 0.5, missing: 'skip',
    note: 'Nyjet LoRaWAN nuk e raportojnë këtë fushë (100% null).'
  },
  {
    key: 'rain', field: 'rain', label: 'Shiu', long: 'Sensori i shiut (raw)',
    unit: 'raw', icon: 'mdi:weather-rainy', dec: 0, public: false,
    desc: 'Dalje analoge e sensorit të shiut. Nuk ka kalibrim mm/h.',
    physMin: 0, physMax: 1100, dispMin: 0, dispMax: 400,
    normal: 400, warn: 600, crit: 800, lowWarn: null,
    gradient: [[0, '#E3C77A'], [0.5, '#38BDF8'], [1, '#1E3A8A']],
    radiusM: 12000, blur: 0.8, opacity: 0.5, missing: 'skip',
    note: 'Nuk publikohet - mungon kalibrimi.'
  }
];

/* ---------------------------------------------------------------- nodes ----
   Identity / dataset facts come from the spreadsheet. Coordinates, station
   names and reporting intervals are operator configuration (the dataset has
   no geometry) and are editable in the admin portal. */
var DEFAULT_NODES = [
  {
    id: 'ND-01', eui: 'A8404172C75D105A', joinEui: 'A840410000000101',
    name: 'Tiranë - 21 Dhjetori', city: 'Tiranë', place: '21_dhjetori',
    address: 'Rr. e Kavajës, zona e 21 Dhjetorit',
    lat: 41.3268, lng: 19.8072, transport: 'LoRaWAN', hw: 'Nyje LoRa (Dragino)',
    installedAt: '2026-02-22', intervalS: 100, active: true, public: true, maintenance: false,
    scale: { snd: 1023, uv: 1023, rain: 1023 },
    sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
    apiId: 'lora/A8404172C75D105A', tz: 'Europe/Tirane',
    notes: 'Nyja me histori më të gjatë (112.837 matje). Sensori PM raporton null në ~4.7% të paketave.'
  },
  {
    id: 'ND-02', eui: 'A84041DA335D105B', joinEui: 'A840410000000101',
    name: 'Tiranë - Universitet', city: 'Tiranë', place: 'upt_campus_universitar',
    address: 'Universiteti Politeknik i Tiranës, Sheshi Nënë Tereza',
    lat: 41.3186, lng: 19.8202, transport: 'LoRaWAN', hw: 'Nyje LoRa (Dragino)',
    installedAt: '2026-03-01', intervalS: 150, active: true, public: true, maintenance: false,
    scale: { snd: 1023, uv: 1023, rain: 1023 },
    sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
    apiId: 'lora/A84041DA335D105B', tz: 'Europe/Tirane',
    notes: 'Sensori UV raporton mesatarisht 997/1023 - i ngopur. Vlerat UV janë shënuar si të pavlefshme.'
  },
  {
    id: 'ND-03', eui: 'raspberrypi_korce_1', joinEui: null,
    name: 'Korçë - Shtëpi Qendër', city: 'Korçë', place: 'korce_qender',
    address: 'Lagjja 8, Korçë', lat: 40.6186, lng: 20.7808,
    transport: 'Wi-Fi / HTTP', hw: 'Raspberry Pi + SDS011 + BME280',
    installedAt: '2026-04-24', intervalS: 102, active: true, public: true, maintenance: false,
    scale: { snd: 255, uv: 255, rain: 255 },
    sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain', 'pres'],
    apiId: 'rpi/korce_1', tz: 'Europe/Tirane',
    notes: 'Zëvendëson nyjen e vjetër në të njëjtën adresë. Raporton 0.0 për temperaturë/lagështi kur sensori dështon.'
  },
  {
    id: 'ND-04', eui: 'raspberrypi_Korca_Universiteti', joinEui: null,
    name: 'Korçë - Universitet', city: 'Korçë', place: null,
    address: 'Universiteti "Fan S. Noli", Bulevardi Rilindasit, Korçë', lat: 40.6142, lng: 20.7846,
    transport: 'Wi-Fi / HTTP', hw: 'Raspberry Pi + SDS011 + BME280',
    installedAt: '2026-04-23', intervalS: 180, active: true, public: true, maintenance: false,
    scale: { snd: 255, uv: 255, rain: 255 },
    sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain', 'pres'],
    apiId: 'rpi/korca_universiteti', tz: 'Europe/Tirane',
    notes: 'Presioni ~920 hPa përputhet me lartësinë ~850 m të Korçës.'
  },
  {
    id: 'ND-05', eui: 'raspberrypi_elb_nyja2', joinEui: null,
    name: 'Elbasan - Shtëpi Unaza', city: 'Elbasan', place: null,
    address: 'Rr. Rinia, Elbasan', lat: 41.0984, lng: 20.1012,
    transport: 'Wi-Fi / HTTP', hw: 'Raspberry Pi + SDS011',
    installedAt: '2026-04-10', intervalS: 805, active: true, public: true, maintenance: false,
    scale: { snd: 255, uv: 255, rain: 255 },
    sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
    apiId: 'rpi/elb_nyja2', tz: 'Europe/Tirane',
    notes: 'Interval i gjerë raportimi (≈13 min). Lagështia mesatare 11% - sensori dyshohet i dëmtuar.'
  },
  {
    id: 'ND-06', eui: 'raspberrypi_elb_universiteti', joinEui: null,
    name: 'Elbasan - Universitet', city: 'Elbasan', place: null,
    address: 'Universiteti "Aleksandër Xhuvani", Elbasan', lat: 41.1125, lng: 20.0822,
    transport: 'Wi-Fi / HTTP', hw: 'Raspberry Pi + SDS011',
    installedAt: '2026-04-10', intervalS: 362, active: true, public: true, maintenance: false,
    scale: { snd: 255, uv: 255, rain: 255 },
    sensors: ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'rain'],
    apiId: 'rpi/elb_universiteti', tz: 'Europe/Tirane',
    notes: 'Nyja e dytë e Elbasanit, në kampusin universitar.'
  }
];

var CITY_CENTER = { 'Tiranë': [41.3235, 19.8154], 'Elbasan': [41.1055, 20.0917], 'Korçë': [40.6186, 20.7793] };

/* ------------------------------------------------------------- settings ---- */
var DEFAULT_SETTINGS = {
  tz: 'Europe/Tirane',
  onlineMult: 2,          // age <= interval * onlineMult  -> online
  delayedMult: 6,         // age <= interval * delayedMult -> delayed, else offline
  validityMin: 180,       // a reading older than this (min) is never shown as "current"
  source: 'dataset',      // dataset | rest | ws   (rest/ws = backend integration points)
  restBase: 'https://api.airmonitor.al/v1',
  wsUrl: 'wss://api.airmonitor.al/v1/stream',
  pollS: 30,
  replay: true,
  replaySpeed: 75,        // dataset seconds per real second
  cursor: '2026-05-29 13:00:00'
};

/* ------------------------------------------------- demo persistence layer ---
   localStorage is a DEMONSTRATION store only. Every write goes through here so
   swapping in a real backend means replacing this object, nothing else. */
var KEY = 'airmonitor.demo.v3';
var store = {
  backend: 'localStorage (demonstrim)',
  read: function () {
    try { return JSON.parse(global.localStorage.getItem(KEY) || '{}') || {}; }
    catch (e) { return {}; }
  },
  write: function (patch) {
    try {
      var cur = store.read();
      for (var k in patch) cur[k] = patch[k];
      global.localStorage.setItem(KEY, JSON.stringify(cur));
      return true;
    } catch (e) { return false; }
  },
  reset: function () { try { global.localStorage.removeItem(KEY); } catch (e) {} }
};

function clone(o) { return JSON.parse(JSON.stringify(o)); }
function mergeById(defaults, saved, idKey) {
  if (!saved || !saved.length) return clone(defaults);
  var out = clone(defaults), map = {};
  out.forEach(function (d) { map[d[idKey]] = d; });
  saved.forEach(function (s) {
    if (map[s[idKey]]) { for (var k in s) map[s[idKey]][k] = s[k]; }
    else out.push(s);
  });
  return out;
}

var saved = store.read();
// A fresh visitor's clock should open right where any AI forecast starts
// (forecastCutoff), or failing that the dataset's own latest hour, rather
// than the bundled demo default; a returning visitor's saved cursor still
// wins. forecastCutoff is preferred over the bare dataset "last" because a
// node can still carry synthetic data that runs a few hours past the real
// history the forecast was actually computed from.
var freshCursor = DS.forecastCutoff || DS.last;
var settingsDefaults = freshCursor ? Object.assign({}, DEFAULT_SETTINGS, { cursor: freshCursor }) : DEFAULT_SETTINGS;
var config = {
  params: mergeById(DEFAULT_PARAMS, saved.params, 'key'),
  nodes: mergeById(DEFAULT_NODES, saved.nodes, 'id'),
  settings: Object.assign({}, settingsDefaults, saved.settings || {})
};
function paramByKey(k) { for (var i = 0; i < config.params.length; i++) if (config.params[i].key === k) return config.params[i]; return null; }
function nodeById(id) { for (var i = 0; i < config.nodes.length; i++) if (config.nodes[i].id === id) return config.nodes[i]; return null; }
function persist() {
  store.write({ params: config.params, nodes: config.nodes, settings: config.settings });
}

/* ------------------------------------------------------------- adapters ----
   The UI only ever talks to `Air.source`. Swapping to a live backend means
   implementing readAt()/history()/meta() against the REST or WS endpoint.   */
function datasetSeries(eui) { return DS.nodes[eui] || null; }

function hourValue(series, key, t) {
  if (!series || !series.hours[key]) return null;
  var arr = series.hours[key];
  var pos = (t - series.h0Ms) / HOUR;
  if (pos < 0 || pos > arr.length - 1) return null;
  var i = Math.floor(pos), f = pos - i;
  var a = arr[i], b = i + 1 < arr.length ? arr[i + 1] : null;
  if (a == null) return null;
  if (b == null || f === 0) return a;
  return a + (b - a) * f;
}
function lastValidBefore(series, key, t, maxBackH) {
  if (!series || !series.hours[key]) return null;
  var arr = series.hours[key];
  var i = Math.min(arr.length - 1, Math.floor((t - series.h0Ms) / HOUR));
  var lim = Math.max(0, i - (maxBackH || 720));
  for (; i >= lim; i--) if (arr[i] != null) return { v: arr[i], t: series.h0Ms + i * HOUR + HOUR / 2 };
  return null;
}
/* deterministic sub-interval jitter so "last packet" ages look real and stable */
function jitter(seedStr, t, mod) {
  var h = 0, s = seedStr + '|' + Math.floor(t / MIN);
  for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h) % mod;
}

var datasetSource = {
  id: 'dataset',
  label: 'Dataset (Excel) - replay',
  detail: DS.source + ' · ' + (DS.rows || 0).toLocaleString('sq-AL') + ' matje · ' + (DS.first || '') + ' → ' + (DS.last || ''),
  live: false,
  range: function () { return { from: parseTs(DS.first), to: parseTs(DS.last) }; },
  /* Snapshot of one node at time t. Returns raw + calibrated values, validity flags. */
  readAt: function (node, t) {
    var s = datasetSeries(node.eui);
    var out = { nodeId: node.id, t: t, packetAt: null, ageMs: null, values: {}, raw: {}, invalid: {}, missing: [] };
    if (!s) { out.noSeries = true; return out; }
    var curH = Math.floor((t - s.h0Ms) / HOUR);
    var hasNow = false, anyKey = null;
    ['snd', 'tmp', 'pm25', 'hum', 'uv'].forEach(function (k) {
      if (s.hours[k] && curH >= 0 && curH < s.hours[k].length && s.hours[k][curH] != null) { hasNow = true; anyKey = anyKey || k; }
    });
    if (hasNow) {
      out.packetAt = t - jitter(node.eui, t, Math.max(30, node.intervalS)) * 1000;
    } else {
      var lv = null;
      ['snd', 'tmp', 'pm25', 'hum', 'uv'].forEach(function (k) {
        var r = lastValidBefore(s, k, t, 4000);
        if (r && (!lv || r.t > lv.t)) lv = r;
      });
      out.packetAt = lv ? lv.t : null;
    }
    out.ageMs = out.packetAt == null ? null : Math.max(0, t - out.packetAt);
    config.params.forEach(function (p) {
      if (node.sensors.indexOf(p.key) < 0) return;
      var raw = hasNow ? hourValue(s, p.field, t) : null;
      if (raw == null) { out.missing.push(p.key); out.values[p.key] = null; out.raw[p.key] = null; return; }
      out.raw[p.key] = raw;
      var v = calibrate(node, p, raw);
      out.values[p.key] = v;
      var bad = validity(node, p, v, raw);
      if (bad) out.invalid[p.key] = bad;
    });
    return out;
  },
  /* Hourly history: n points ending at t. */
  history: function (node, paramKey, t, hours) {
    var s = datasetSeries(node.eui), p = paramByKey(paramKey), out = [];
    if (!s || !p) return out;
    var end = Math.floor((t - s.h0Ms) / HOUR);
    for (var i = end - hours + 1; i <= end; i++) {
      var raw = (s.hours[p.field] && i >= 0 && i < s.hours[p.field].length) ? s.hours[p.field][i] : null;
      out.push({ t: s.h0Ms + i * HOUR, v: raw == null ? null : calibrate(node, p, raw) });
    }
    return out;
  },
  daily: function (node, paramKey) {
    var s = datasetSeries(node.eui), p = paramByKey(paramKey);
    if (!s || !p || !s.daily[p.field]) return [];
    return s.days.map(function (d, i) {
      var raw = s.daily[p.field][i];
      return { day: d, v: raw == null ? null : calibrate(node, p, raw) };
    });
  },
  diurnal: function (node, paramKey) {
    var s = datasetSeries(node.eui), p = paramByKey(paramKey);
    if (!s || !p || !s.diurnal[p.field]) return null;
    return s.diurnal[p.field].map(function (raw) { return raw == null ? null : calibrate(node, p, raw); });
  },
  meta: function (node) { return datasetSeries(node.eui) || {}; },
  packets: function (node) {
    var s = datasetSeries(node.eui);
    return s ? s.tail.slice().reverse() : [];
  }
};

/* Backend integration point - not wired to a server in this build. */
function restSource(base) {
  return {
    id: 'rest', label: 'REST API', detail: base, live: true, notImplemented: true,
    range: datasetSource.range,
    readAt: function () { throw new Error('Air.source REST: implemento GET ' + base + '/nodes/{id}/latest'); },
    history: function () { throw new Error('Air.source REST: implemento GET ' + base + '/nodes/{id}/history'); },
    daily: function () { return []; }, diurnal: function () { return null; },
    meta: function () { return {}; }, packets: function () { return []; }
  };
}

/* --------------------------------------------------- calibration / QA ----- */
function calibrate(node, p, raw) {
  if (raw == null) return null;
  var v = raw;
  if ((p.key === 'snd' || p.key === 'uv' || p.key === 'rain') && node.scale && node.scale[p.key]) {
    if (p.key !== 'rain') v = raw / node.scale[p.key] * 100;         // raw → % of sensor scale
  }
  if (node.cal && node.cal[p.key]) {
    var c = node.cal[p.key];
    if (c.mult != null) v = v * c.mult;
    if (c.offset != null) v = v + c.offset;
  }
  return Math.round(v * 1000) / 1000;
}
/* Returns a reason string when a value must not be treated as a measurement. */
function validity(node, p, v, raw) {
  if (v == null) return 'null';
  if (v < p.physMin || v > p.physMax) return 'jashtë intervalit fizik';
  if ((p.key === 'tmp' || p.key === 'hum') && raw === 0) return 'vlerë sentinel 0.0';
  if (p.key === 'uv' && v >= 98) return 'sensor i ngopur';
  return null;
}

/* --------------------------------------------------------------- status ---- */
function statusOf(node, snap, t) {
  if (!node.active) return 'inactive';
  if (node.maintenance) return 'maintenance';
  if (snap.ageMs == null) return 'nodata';
  var iv = node.intervalS * 1000;
  if (snap.ageMs <= iv * config.settings.onlineMult) return 'online';
  if (snap.ageMs <= iv * config.settings.delayedMult) return 'delayed';
  return 'offline';
}
var STATUS = {
  online:      { label: 'Online',        icon: 'solar:check-circle-bold',        fg: '#1F8A4C', bg: '#F0FDF4', dot: '#22A65A' },
  delayed:     { label: 'Me vonesë',     icon: 'solar:clock-circle-bold',        fg: '#9A5B00', bg: '#FEF6E7', dot: '#F79009' },
  offline:     { label: 'Offline',       icon: 'solar:close-circle-bold',        fg: '#B1322F', bg: '#F7EDED', dot: '#B1322F' },
  nodata:      { label: 'Pa të dhëna',   icon: 'solar:minus-circle-bold',        fg: '#72767F', bg: '#F2F2F2', dot: '#979797' },
  inactive:    { label: 'Jashtë shërbimi', icon: 'solar:power-bold',             fg: '#72767F', bg: '#F2F2F2', dot: '#B8BDC4' },
  maintenance: { label: 'Në mirëmbajtje', icon: 'solar:settings-bold',           fg: '#4976F4', bg: '#EAF0FE', dot: '#4976F4' }
};
var SEVERITY = {
  info:     { label: 'Informacion', fg: '#4976F4', bg: '#EAF0FE', icon: 'solar:info-circle-bold', rank: 1 },
  warning:  { label: 'Kujdes',      fg: '#9A5B00', bg: '#FEF6E7', icon: 'solar:danger-triangle-bold', rank: 2 },
  critical: { label: 'Kritik',      fg: '#B1322F', bg: '#F7EDED', icon: 'solar:danger-bold', rank: 3 }
};
/* Environmental grade of one value against its configured thresholds. */
function grade(p, v) {
  if (v == null) return { key: 'nodata', label: 'Pa të dhëna', fg: '#72767F', bg: '#F2F2F2' };
  if (p.crit != null && v >= p.crit) return { key: 'critical', label: 'Kritik', fg: '#B1322F', bg: '#F7EDED' };
  if (p.warn != null && v >= p.warn) return { key: 'warning', label: 'Kujdes', fg: '#9A5B00', bg: '#FEF6E7' };
  if (p.lowWarn != null && v <= p.lowWarn) return { key: 'low', label: 'I ulët', fg: '#4976F4', bg: '#EAF0FE' };
  if (p.normal != null && v >= p.normal) return { key: 'moderate', label: 'I moderuar', fg: '#C77A00', bg: '#FEF6E7' };
  return { key: 'normal', label: 'Normal', fg: '#1F8A4C', bg: '#F0FDF4' };
}

/* --------------------------------------------------------- air quality ----- */
function aqiFromPm25(pm) {
  if (pm == null) return { v: null, label: 'Pa të dhëna', lvl: -1, color: '#979797', bg: '#F2F2F2', light: '#B8BDC4' };
  var a;
  if (pm <= 12) a = pm / 12 * 50;
  else if (pm <= 35.4) a = 50 + (pm - 12) / 23.4 * 50;
  else if (pm <= 55.4) a = 100 + (pm - 35.4) / 20 * 50;
  else if (pm <= 150.4) a = 150 + (pm - 55.4) / 95 * 100;
  else a = Math.min(500, 250 + (pm - 150.4) / 100 * 100);
  a = Math.round(a);
  var L = [
    { m: 50,  c: '#1F8A4C', b: '#F0FDF4', l: 'I mirë',      lt: '#4ADE80' },
    { m: 100, c: '#C77A00', b: '#FEF6E7', l: 'I moderuar',  lt: '#FBBF56' },
    { m: 150, c: '#DA6A00', b: '#FDF0E4', l: 'I ndjeshëm',  lt: '#FB9245' },
    { m: 200, c: '#B1322F', b: '#F7EDED', l: 'I dëmshëm',   lt: '#F87171' },
    { m: 1e9, c: '#6D28D9', b: '#F1ECFB', l: 'Rrezik',      lt: '#C4B5FD' }
  ];
  var i = 0; while (a > L[i].m) i++;
  return { v: a, label: L[i].l, lvl: i, color: L[i].c, bg: L[i].b, light: L[i].lt };
}

/* ------------------------------------------------------------- gradient ---- */
function hex2rgb(h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; }
function rampColor(p, t) {
  var g = p.gradient; t = Math.max(0, Math.min(1, t));
  for (var i = 1; i < g.length; i++) {
    if (t <= g[i][0]) {
      var a = g[i - 1], b = g[i], f = (t - a[0]) / (b[0] - a[0] || 1);
      var ca = hex2rgb(a[1]), cb = hex2rgb(b[1]);
      return [Math.round(ca[0] + (cb[0] - ca[0]) * f), Math.round(ca[1] + (cb[1] - ca[1]) * f), Math.round(ca[2] + (cb[2] - ca[2]) * f)];
    }
  }
  return hex2rgb(g[g.length - 1][1]);
}
function rampCss(p) {
  return 'linear-gradient(90deg,' + p.gradient.map(function (s) { return s[1] + ' ' + Math.round(s[0] * 100) + '%'; }).join(',') + ')';
}
function normVal(p, v) { return (v - p.dispMin) / (p.dispMax - p.dispMin); }
function colorFor(p, v) { var c = rampColor(p, normVal(p, v)); return 'rgb(' + c[0] + ',' + c[1] + ',' + c[2] + ')'; }
function fmtVal(p, v) { return v == null ? '-' : (p.dec ? v.toFixed(p.dec) : String(Math.round(v))); }

/* ----------------------------------------------------------------- clock ---- */
var clock = {
  t: parseTs(config.settings.cursor),
  playing: false,
  _timer: null,
  _subs: [],
  set: function (t) {
    var r = source().range();
    clock.t = Math.max(r.from, Math.min(r.to, t));
    clock.emit('set');
  },
  play: function () {
    if (clock.playing) return;
    clock.playing = true;
    clock._timer = setInterval(function () {
      var r = source().range();
      var next = clock.t + config.settings.replaySpeed * 1000;
      if (next >= r.to) { next = r.to; clock.pause(); }
      clock.t = next; clock.emit('tick');
    }, 1000);
    clock.emit('state');
  },
  pause: function () {
    clock.playing = false;
    if (clock._timer) clearInterval(clock._timer);
    clock._timer = null; clock.emit('state');
  },
  toggle: function () { clock.playing ? clock.pause() : clock.play(); },
  on: function (fn) { clock._subs.push(fn); },
  emit: function (kind) { clock._subs.forEach(function (f) { try { f(clock.t, kind); } catch (e) { console.warn('clock subscriber', e); } }); }
};

var _source = datasetSource;
function source() { return _source; }
function setSource(id) {
  _source = id === 'rest' ? restSource(config.settings.restBase) : datasetSource;
  config.settings.source = id; persist();
}

/* -------------------------------------------------------------- snapshot ---- */
function snapshot(t) {
  t = t == null ? clock.t : t;
  var out = { t: t, nodes: [], byId: {}, cities: {} };
  config.nodes.forEach(function (n) {
    var snap;
    try { snap = source().readAt(n, t); }
    catch (e) { snap = { nodeId: n.id, t: t, packetAt: null, ageMs: null, values: {}, raw: {}, invalid: {}, missing: [], error: e.message }; }
    snap.node = n;
    snap.status = statusOf(n, snap, t);
    snap.fresh = snap.ageMs != null && snap.ageMs <= config.settings.validityMin * MIN;
    snap.usable = (snap.status === 'online' || snap.status === 'delayed') && snap.fresh;
    var worst = 'normal', sensors = 0, ok = 0;
    config.params.forEach(function (p) {
      if (n.sensors.indexOf(p.key) < 0) return;
      sensors++;
      var v = snap.values[p.key];
      if (v != null && !snap.invalid[p.key]) {
        ok++;
        var g = grade(p, v);
        if (g.key === 'critical') worst = 'critical';
        else if (g.key === 'warning' && worst !== 'critical') worst = 'warning';
      }
    });
    snap.quality = sensors ? ok / sensors : 0;
    snap.envGrade = snap.usable ? worst : 'nodata';
    /* the value shown for a node when it is not currently reporting */
    if (!snap.usable) {
      snap.lastKnown = {};
      config.params.forEach(function (p) {
        if (n.sensors.indexOf(p.key) < 0) return;
        var s = datasetSeries(n.eui);
        var lv = lastValidBefore(s, p.field, t, 4000);
        snap.lastKnown[p.key] = lv ? { v: calibrate(n, p, lv.v), t: lv.t } : null;
      });
    }
    out.nodes.push(snap); out.byId[n.id] = snap;
  });
  Object.keys(CITY_CENTER).forEach(function (c) {
    var ns = out.nodes.filter(function (s) { return s.node.city === c && s.node.public; });
    var live = ns.filter(function (s) { return s.usable; });
    out.cities[c] = { name: c, nodes: ns, live: live, center: CITY_CENTER[c] };
  });
  return out;
}
function cityAvg(snap, city, key) {
  var vals = snap.nodes.filter(function (s) {
    return s.node.city === city && s.node.public && s.usable && s.values[key] != null && !s.invalid[key];
  }).map(function (s) { return s.values[key]; });
  if (!vals.length) return null;
  return vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
}
function netAvg(snap, key) {
  var vals = snap.nodes.filter(function (s) {
    return s.node.public && s.usable && s.values[key] != null && !s.invalid[key];
  }).map(function (s) { return s.values[key]; });
  if (!vals.length) return null;
  return vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
}
/* Points feeding a heatmap layer: only valid, fresh readings. */
function heatPoints(snap, key) {
  return snap.nodes.filter(function (s) {
    return s.node.public && s.usable && s.values[key] != null && !s.invalid[key];
  }).map(function (s) { return { lat: s.node.lat, lng: s.node.lng, v: s.values[key], id: s.node.id }; });
}

/* Real AI-model forecast for a single node, straight from the backend's
   Forecast table (see monitoring/dataset.py: build_node_series -> forecast).
   Only used when the requested window [t, t+leadH] is fully covered by the
   stored forecast; otherwise the caller falls back to the client heuristic
   below (e.g. before the model has run, or once the 72h window has aged out). */
function realForecast(node, p, t, leadH) {
  var s = datasetSeries(node.eui);
  var series = s && s.forecast && s.forecast[p.field];
  if (!series || !series.length) return null;
  var pts = series.filter(function (d) { return d.t > t && d.t <= t + leadH * HOUR; });
  if (pts.length < leadH) return null;
  return pts.map(function (d) { return { t: d.t, v: d.v, lo: d.lo, hi: d.hi, conf: 80 }; });
}

/* -------------------------------------------------------------- forecast ----
   Prefers the trained model's own forecast (realForecast) for a single node
   when it covers the requested window. Otherwise: persistence + the node's
   own measured diurnal cycle (from 290k rows) + a mild synoptic drift derived
   from the last 24h trend. Uncertainty widens with lead time. Observed and
   forecast points are returned separately. */
function forecastFor(nodeIds, paramKey, t, leadH) {
  leadH = leadH || 72;
  var p = paramByKey(paramKey);
  var nodes = nodeIds.map(nodeById).filter(Boolean);
  if (!nodes.length || !p) return null;
  var hist = [], prof = new Array(24).fill(0), profN = new Array(24).fill(0);
  for (var h = -47; h <= 0; h++) {
    var vals = [];
    nodes.forEach(function (n) {
      var s = datasetSeries(n.eui);
      var v = hourValue(s, p.field, t + h * HOUR);
      if (v != null) vals.push(calibrate(n, p, v));
    });
    hist.push({ t: t + h * HOUR, v: vals.length ? vals.reduce(function (a, b) { return a + b; }) / vals.length : null });
  }
  nodes.forEach(function (n) {
    var d = source().diurnal(n, paramKey);
    if (!d) return;
    d.forEach(function (v, i) { if (v != null) { prof[i] += v; profN[i]++; } });
  });
  var profile = prof.map(function (s, i) { return profN[i] ? s / profN[i] : null; });
  var profMean = 0, pn = 0;
  profile.forEach(function (v) { if (v != null) { profMean += v; pn++; } });
  profMean = pn ? profMean / pn : 1;
  var known = hist.filter(function (d) { return d.v != null; });
  if (!known.length) return null;
  var cur = known[known.length - 1].v;
  var recent = known.slice(-6), older = known.slice(-24, -18);
  var trend = (recent.length && older.length)
    ? (recent.reduce(function (a, b) { return a + b.v; }, 0) / recent.length) -
      (older.reduce(function (a, b) { return a + b.v; }, 0) / older.length) : 0;
  var curH = new Date(t).getUTCHours();
  var anchor = profile[curH] != null ? profile[curH] : profMean;
  var scale = anchor > 0.01 ? cur / anchor : 1;
  scale = Math.max(0.35, Math.min(2.8, scale));
  var real = nodes.length === 1 ? realForecast(nodes[0], p, t, leadH) : null;
  var fut = real;
  if (!fut) {
    fut = [];
    for (var i = 1; i <= leadH; i++) {
      var tt = t + i * HOUR, hh = new Date(tt).getUTCHours();
      var base = profile[hh] != null ? profile[hh] : profMean;
      var relax = Math.exp(-i / 30);                       // persistence decays toward climatology
      var v = base * (1 + (scale - 1) * relax) + trend * 0.28 * relax;
      if (p.key !== 'tmp') v = Math.max(p.physMin, v);
      var band = Math.abs(v) * (0.08 + 0.011 * i) + (p.dispMax - p.dispMin) * 0.008 * Math.sqrt(i);
      fut.push({ t: tt, v: v, lo: v - band, hi: v + band, conf: Math.max(35, Math.round(96 - i * 0.72)) });
    }
  }
  return {
    param: p, cur: cur, hist: hist, fut: fut, trend: trend, profile: profile, nodes: nodes,
    source: real ? 'model' : 'heuristic',
    modelName: real && nodes.length === 1 ? ((datasetSeries(nodes[0].eui).forecastMeta || {}).models || {})[p.field] : null,
  };
}
function bestWindow(fc) {
  if (!fc) return null;
  var best = null;
  for (var i = 0; i + 2 < Math.min(24, fc.fut.length); i++) {
    var m = (fc.fut[i].v + fc.fut[i + 1].v + fc.fut[i + 2].v) / 3;
    if (!best || m < best.m) best = { m: m, i: i };
  }
  if (!best) return null;
  return {
    from: fc.fut[best.i].t, to: fc.fut[best.i + 2].t + HOUR, val: best.m,
    betterThanNow: best.m < fc.cur * 0.95
  };
}
function dayOutlook(fc) {
  if (!fc) return [];
  var out = [], day = null;
  fc.fut.forEach(function (d) {
    var k = new Date(d.t).toISOString().slice(0, 10);
    if (!day || day.key !== k) { day = { key: k, t: d.t, vals: [], conf: [] }; out.push(day); }
    day.vals.push(d.v); day.conf.push(d.conf);
  });
  return out.slice(0, 3).map(function (d, i) {
    var avg = d.vals.reduce(function (a, b) { return a + b; }, 0) / d.vals.length;
    return {
      t: d.t, label: i === 0 ? 'Sot' : i === 1 ? 'Nesër' : 'Pasnesër',
      dayName: fmtDayName(d.t), date: fmtDate(d.t),
      avg: avg, min: Math.min.apply(null, d.vals), max: Math.max.apply(null, d.vals),
      conf: Math.round(d.conf.reduce(function (a, b) { return a + b; }, 0) / d.conf.length)
    };
  });
}


/* --------------------------------------------- IDW heatmap layer (Leaflet) --
   True value interpolation between stations (inverse distance weighting) -
   not a point-density heatmap. Coverage alpha falls off with distance so
   unmonitored regions are never painted as if they were measured.          */
function idwLayer(L, opts) {
  var Layer = L.Layer.extend({
    initialize: function (o) { this.o = Object.assign({ step: 5, power: 2.4, opacity: 0.7, radiusM: 5000, blur: 0.6 }, o || {}); this.points = []; },
    onAdd: function (map) {
      this._map = map;
      var c = this._canvas = L.DomUtil.create('canvas', 'air-idw');
      c.style.position = 'absolute'; c.style.pointerEvents = 'none';
      c.style.willChange = 'transform';
      map.getPane('overlayPane').appendChild(c);
      map.on('moveend zoomend resize', this._reset, this);
      if (map.options.zoomAnimation && L.Browser.any3d) map.on('zoomanim', this._animateZoom, this);
      this._reset();
    },
    onRemove: function (map) {
      if (this._canvas && this._canvas.parentNode) this._canvas.parentNode.removeChild(this._canvas);
      map.off('moveend zoomend resize', this._reset, this);
      map.off('zoomanim', this._animateZoom, this);
      this._canvas = null;
    },
    setPoints: function (pts) { this.points = pts || []; this._draw(); return this; },
    setOptions: function (o) { Object.assign(this.o, o || {}); this._draw(); return this; },
    _animateZoom: function (e) {
      if (!this._canvas) return;
      var scale = this._map.getZoomScale(e.zoom), off = this._map._latLngBoundsToNewLayerBounds(this._map.getBounds(), e.zoom, e.center).min;
      L.DomUtil.setTransform(this._canvas, off, scale);
    },
    _reset: function () {
      if (!this._canvas || !this._map) return;
      var size = this._map.getSize(), tl = this._map.containerPointToLayerPoint([0, 0]);
      L.DomUtil.setTransform(this._canvas, tl, 1);
      var dpr = 1; // low-res buffer, upscaled - heatmaps do not need device pixels
      this._canvas.width = Math.max(1, Math.ceil(size.x / this.o.step));
      this._canvas.height = Math.max(1, Math.ceil(size.y / this.o.step));
      this._canvas.style.width = size.x + 'px';
      this._canvas.style.height = size.y + 'px';
      this._draw();
    },
    _draw: function () {
      var cv = this._canvas, map = this._map;
      if (!cv || !map) return;
      var w = cv.width, h = cv.height, ctx = cv.getContext('2d');
      ctx.clearRect(0, 0, w, h);
      cv.style.opacity = this.o.opacity;
      var pts = (this.points || []).filter(function (p) { return p && isFinite(p.v); });
      if (!pts.length) return;
      var step = this.o.step, P = this.o.power, p = this.o.param;
      /* Radius in screen pixels. A small zoom-out boost keeps the field legible
         at country level without pretending a station measures a whole region. */
      var c = map.getCenter(), z = map.getZoom();
      var mPerPx = 40075016.686 * Math.cos(c.lat * Math.PI / 180) / Math.pow(2, z + 8);
      var boost = z >= 12 ? 1 : Math.min(2.2, 1 + (12 - z) * 0.22);
      var rPx = this.o.radiusM * boost / mPerPx;
      rPx = Math.max(26, Math.min(320, rPx)) / step;
      var soft = 0.30 + this.o.blur * 0.42;
      var sp = pts.map(function (q) {
        var pt = map.latLngToContainerPoint([q.lat, q.lng]);
        return { x: pt.x / step, y: pt.y / step, v: q.v };
      });
      var img = ctx.createImageData(w, h), d = img.data;
      var lut = new Uint8ClampedArray(257 * 3);
      for (var i = 0; i <= 256; i++) { var col = rampColor(p, i / 256); lut[i * 3] = col[0]; lut[i * 3 + 1] = col[1]; lut[i * 3 + 2] = col[2]; }
      var lo = p.dispMin, span = (p.dispMax - p.dispMin) || 1;
      var r2max = rPx * rPx * 7;
      for (var y = 0; y < h; y++) {
        for (var x = 0; x < w; x++) {
          var num = 0, den = 0, cov = 0;
          for (var k = 0; k < sp.length; k++) {
            var dx = x - sp[k].x, dy = y - sp[k].y, r2 = dx * dx + dy * dy;
            if (r2 > r2max) continue;
            var wgt = 1 / Math.pow(r2 + 4, P / 2);
            num += sp[k].v * wgt; den += wgt;
            var cc = Math.exp(-r2 / (2 * rPx * rPx * soft));
            if (cc > cov) cov = cc;
          }
          if (!den || cov < 0.045) continue;
          var val = num / den;
          var tnorm = (val - lo) / span;
          tnorm = tnorm < 0 ? 0 : tnorm > 1 ? 1 : tnorm;
          var li = (tnorm * 256) | 0, o = (y * w + x) * 4;
          d[o] = lut[li * 3]; d[o + 1] = lut[li * 3 + 1]; d[o + 2] = lut[li * 3 + 2];
          d[o + 3] = Math.min(255, cov * 255 * 1.35) | 0;
        }
      }
      ctx.putImageData(img, 0, 0);
    }
  });
  return new Layer(opts);
}

/* ----------------------------------------------------------------- export -- */
global.Air = Object.assign(global.Air || {}, {
  DS: DS, HOUR: HOUR, MIN: MIN,
  DEFAULT_PARAMS: DEFAULT_PARAMS, DEFAULT_NODES: DEFAULT_NODES,
  DEFAULT_SETTINGS: DEFAULT_SETTINGS,
  CITY_CENTER: CITY_CENTER, STATUS: STATUS, SEVERITY: SEVERITY,
  config: config, store: store, persist: persist, clone: clone,
  paramByKey: paramByKey, nodeById: nodeById,
  publicParams: function () { return config.params.filter(function (p) { return p.public; }); },
  source: source, setSource: setSource, restSource: restSource, datasetSource: datasetSource,
  clock: clock, snapshot: snapshot, cityAvg: cityAvg, netAvg: netAvg, heatPoints: heatPoints,
  statusOf: statusOf, grade: grade, aqi: aqiFromPm25, calibrate: calibrate, validity: validity,
  rampColor: rampColor, rampCss: rampCss, colorFor: colorFor, normVal: normVal, fmtVal: fmtVal,
  forecast: forecastFor, bestWindow: bestWindow, dayOutlook: dayOutlook,
  parseTs: parseTs, fmtTime: fmtTime, fmtDate: fmtDate, fmtDateTime: fmtDateTime,
  fmtDayName: fmtDayName, fmtAge: fmtAge,
  idwLayer: idwLayer
});
/* if the extensions were loaded first (script order can vary), re-apply them */
if (global.__airExtraSrc && !global.Air.cities) {
  var s = document.createElement('script');
  s.src = global.__airExtraSrc;
  document.head.appendChild(s);
}
})(window);
