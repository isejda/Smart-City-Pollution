/* ==========================================================================
   Smart City Pollution - brand, bilingual layer, analytics & reporting.
   Loaded AFTER air-core.js by both portals. Patches window.Air in place.
   ========================================================================== */
(function (global) {
'use strict';
var A = global.Air;
if (!A) { console.error('air-extra.js requires air-core.js'); return; }
/* remember where we live, so air-core.js can pull us back in if it is
   evaluated after us and rebuilds the namespace */
try {
  var here = document.currentScript && document.currentScript.src;
  if (here) global.__airExtraSrc = here;
} catch (err) {}
/* applying twice would double-wrap A.evaluate and duplicate every e-mail */
if (A.__extra) return;
A.__extra = true;

var HOUR = A.HOUR, DAY = 24 * HOUR;

/* ------------------------------------------------------------------ brand --
   Simple geometric mark: a rounded tile holding a three-bar skyline with a
   sensor dot and two air waves. Renders at any size, single accent colour.  */
function logoMark(size, ink, accent) {
  size = size || 36; ink = ink || '#08514A'; accent = accent || '#0E6A60';
  var s = size / 40;
  return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 40 40" fill="none" aria-hidden="true" style="flex-shrink:0">' +
    '<g transform="rotate(128 20 20)">' +
      '<circle cx="20" cy="20" r="16.4" stroke="' + ink + '" stroke-opacity=".24" stroke-width="' + (1.9 / Math.max(0.7, s)).toFixed(2) + '" stroke-linecap="round" stroke-dasharray="80 23"/>' +
      '<circle cx="20" cy="20" r="9.7" stroke="' + accent + '" stroke-opacity=".62" stroke-width="' + (2.2 / Math.max(0.7, s)).toFixed(2) + '" stroke-linecap="round" stroke-dasharray="47 14"/>' +
    '</g>' +
    '<circle cx="20" cy="20" r="3.9" fill="' + accent + '"/>' +
    '</svg>';
}
function logoLockup(o) {
  o = o || {};
  var size = o.size || 34, dark = !!o.onDark, fs = o.fs || 15.5;
  return '<span style="display:flex;align-items:center;gap:11px">' +
    logoMark(size, dark ? '#FFFFFF' : '#08514A', dark ? '#7ED0C2' : '#0E6A60') +
    '<span style="display:flex;flex-direction:column;line-height:1">' +
      '<span style="font-family:var(--font-display);font-weight:600;font-size:' + fs + 'px;letter-spacing:-.03em;color:' + (dark ? '#fff' : 'var(--text-primary)') + '">Smart City</span>' +
      '<span style="font-size:' + (fs - 6) + 'px;font-weight:700;letter-spacing:.2em;margin-top:3px;color:' + (dark ? '#7ED0C2' : 'var(--teal-500)') + '">POLLUTION</span>' +
    '</span></span>';
}
A.logoMark = logoMark; A.logoLockup = logoLockup;
A.brand = { name: 'Smart City Pollution', short: 'SmartCity Pollution' };

/* ------------------------------------------------------------------- i18n -- */
var DICT = {
  /* chrome */
  nav_map: ['Harta', 'Map'], nav_trends: ['Trendet', 'Trends'], nav_advice: ['Këshilla', 'Advice'],
  nav_about: ['Projekti', 'Project'], staff_login: ['Hyrje për stafin', 'Staff sign-in'],
  lang_label: ['Gjuha', 'Language'],
  /* hero */
  hero_cta_map: ['Shiko hartën', 'Open the map'], hero_cta_learn: ['Më shumë', 'Learn more'],
  h1_eyebrow: ['PROJEKTI', 'THE PROJECT'],
  h1_t: ['Ajri i qytetit, i matur çdo minutë', 'City air, measured every minute'],
  h1_b: ['Një rrjet nyjesh me kosto të ulët mat grimcat, temperaturën, lagështinë, zhurmën dhe UV-në në Tiranë, Korçë dhe Elbasan - dhe i publikon të dhënat pa filtër.', 'A low-cost sensor network measures particulates, temperature, humidity, noise and UV in Tirana, Korça and Elbasan - and publishes the readings unfiltered.'],
  h2_eyebrow: ['MBULIMI', 'COVERAGE'],
  h2_t: ['Matje lokale, jo mesatare qyteti', 'Local readings, not city averages'],
  h2_b: ['Çdo nyje mbulon një zonë prej rreth 150 metrash. Ngjyra në hartë tregon vetëm atë që nyja mat me të vërtetë - asgjë nuk interpolohet mbi zona pa sensorë.', 'Each node covers roughly a 150-metre area. The colour on the map shows only what the node actually measures - nothing is interpolated over unmonitored ground.'],
  h3_eyebrow: ['TRANSPARENCA', 'TRANSPARENCY'],
  h3_short: ['TË DHËNAT', 'THE DATA'],
  h3_t: ['Të dhëna të hapura, në kohë reale', 'Open data, in real time'],
  h3_b: ['{rows} matje nga {nodes} nyje janë të aksesueshme për këdo: qytetarë, gazetarë, kërkues dhe institucione. E njëjta pamje që sheh operatori, e sheh edhe publiku.', '{rows} measurements from {nodes} nodes are available to anyone: citizens, journalists, researchers and institutions. The public sees exactly what the operator sees.'],
  h4_eyebrow: ['QËLLIMI', 'THE GOAL'],
  h4_t: ['Nga matja te vendimi', 'From measurement to decision'],
  h4_b: ['Të dhënat shërbejnë për të mbrojtur grupet e ndjeshme, për të vlerësuar politikat lokale dhe për të ndërtuar një bazë provash për cilësinë e ajrit në Shqipëri.', 'The data protects sensitive groups, evaluates local policy and builds an evidence base for air quality in Albania.'],
  stat_nodes: ['nyje aktive', 'active nodes'], stat_cities: ['qytete', 'cities'],
  stat_rows: ['matje të regjistruara', 'recorded measurements'], stat_params: ['parametra', 'parameters'],
  stat_cover: ['m rreze mbulimi', 'm coverage radius'], stat_open: ['të dhëna të hapura', 'open data'],
  /* map */
  map_title: ['Harta e matjeve', 'Measurement map'],
  map_sub: ['Zgjidh qytetin, pastaj kliko një nyje për detajet e saj.', 'Pick a city, then click a node for its details.'],
  all_cities: ['Të gjitha', 'All cities'],
  param: ['Parametri', 'Parameter'], hide_panels: ['Fshih panelet', 'Hide panels'], show_panels: ['Shfaq panelet', 'Show panels'],
  legend: ['Legjenda', 'Legend'], active: ['Aktive', 'Active'], inactive: ['Joaktive', 'Inactive'],
  nodes_shown: ['nyje në pamje', 'nodes in view'], no_nodes: ['Asnjë nyje në këtë qytet', 'No nodes in this city'],
  recenter: ['Rikthe pamjen', 'Recenter'],
  coverage_note: ['Rrethi tregon zonën ~150 m që mbulon nyja.', 'The circle shows the ~150 m area the node covers.'],
  /* node panel */
  latest: ['Matja e fundit', 'Latest reading'], updated: ['përditësuar', 'updated'], ago: ['më parë', 'ago'],
  d_day: ['Dita', 'Day'], d_week: ['Java', 'Week'], d_month: ['Muaji', 'Month'],
  no_data: ['Pa të dhëna', 'No data'], forecast_72: ['Parashikimi 72-orësh', '72-hour forecast'],
  min: ['min', 'min'], avg: ['mesatare', 'average'], max: ['maks', 'max'],
  address: ['Adresa', 'Address'], tech: ['Teknologjia', 'Technology'], interval: ['Intervali', 'Interval'],
  installed: ['Instaluar', 'Installed'], close: ['Mbyll', 'Close'],
  open_trends: ['Shiko trendet', 'See trends'],
  /* trends */
  tr_title: ['Trendet sipas zonës', 'Trends by area'],
  tr_sub: ['Qyteti është mesatarja e nyjeve të tij. Zgjidh një nyje për ecurinë dhe parashikimin e asaj zone.', 'A city is the average of its nodes. Pick a node for that area’s own history and forecast.'],
  city: ['Qyteti', 'City'], node: ['Nyja', 'Node'], city_avg: ['Mesatarja e qytetit', 'City average'],
  period: ['Periudha', 'Period'], forecast: ['Parashikimi', 'Forecast'],
  observed: ['E matur', 'Observed'], predicted: ['E parashikuar', 'Predicted'],
  conf: ['siguri', 'confidence'], best_window: ['Dritarja më e mirë', 'Best window'],
  best_none: ['Asnjë përmirësim i qartë në 24 orët e ardhshme.', 'No clear improvement in the next 24 hours.'],
  /* advice */
  ad_title: ['Çfarë do të thotë kjo për ty', 'What this means for you'],
  ad_sub: ['Këshilla për situatën aktuale në zonat ku po masim. Ndrysho qytetin për të parë kushtet lokale.', 'Advice for the current situation where we measure. Switch city to see local conditions.'],
  aud_all: ['Të gjithë', 'Everyone'], aud_kids: ['Fëmijë', 'Children'], aud_old: ['Të moshuar', 'Older adults'],
  aud_sport: ['Sportistë', 'Athletes'], aud_asthma: ['Astmatikë', 'Asthma & COPD'],
  now_in: ['Tani në', 'Right now in'],
  /* about */
  ab_title: ['Rreth projektit', 'About the project'],
  ab_b: ['Smart City Pollution është një rrjet monitorimi i ndërtuar nga një grup kërkimor shqiptar. Nyjet janë me kosto të ulët dhe përdorin dy teknologji: LoRaWAN për zona pa internet dhe Raspberry Pi me API për zona me lidhje fikse.', 'Smart City Pollution is a monitoring network built by an Albanian research group. The nodes are low-cost and use two technologies: LoRaWAN for areas without internet and Raspberry Pi with an HTTP API where fixed connectivity exists.'],
  ab_what: ['Çfarë masim', 'What we measure'],
  disclaimer: ['Zhurma dhe UV raportohen si përqindje e shkallës së sensorit, jo në dB apo Indeks UV - sensorët nuk janë kalibruar akustikisht apo radiometrikisht.', 'Noise and UV are reported as a percentage of sensor scale, not in dB or UV Index - the sensors are not acoustically or radiometrically calibrated.'],
  replay_note: ['Të dhënat riprodhohen nga dataseti i projektit (shkurt–qershor 2026), zona kohore Europe/Tirane.', 'Data is replayed from the project dataset (February–June 2026), Europe/Tirane time zone.'],
  /* hero panes */
  net_numbers: ['RRJETI NË NUMRA', 'THE NETWORK IN NUMBERS'],
  feed_title: ['PAKETAT E FUNDIT', 'LATEST PACKETS'],
  feed_note: ['PM2.5 në µg/m³ · rrjedhë e drejtpërdrejtë e paketave', 'PM2.5 in µg/m³ · live packet stream'],
  cov_title: ['ZONA E MBULUAR', 'COVERED AREA'],
  cov_measured: ['zonë e matur', 'measured area'],
  cov_nosensor: ['nyje fqinje', 'neighbouring node'],
  cov_scale: ['≈150 m rreze', '≈150 m radius'],
  cov_foot: ['Jashtë rrethit nuk pretendojmë asgjë.', 'Outside the circle we claim nothing.'],
  goal_title: ['NGA MATJA TE VENDIMI', 'FROM MEASUREMENT TO DECISION'],
  step1_t: ['Masim', 'We measure'],
  step1_b: ['Të dhëna çdo 5 minuta, drejtë nga terreni.', 'Readings every 5 minutes, straight from the field.'],
  step2_t: ['Publikojmë', 'We publish'],
  step2_b: ['E njejtë pamje për qytetarin dhe operatorin.', 'The same view for citizen and operator.'],
  step3_t: ['Vendosim', 'We decide'],
  step3_b: ['Prova për shtesën e nyjeve dhe politikat lokale.', 'Evidence for new nodes and local policy.'],
  /* footer */
  ft_portal: ['Portali', 'Portal'], ft_data: ['Të dhënat', 'Data'], ft_contact: ['Kontakt', 'Contact'],
  ft_source: ['Burimi', 'Source'], ft_range: ['Periudha', 'Range'], ft_tz: ['Zona kohore', 'Time zone'],
  ft_rights: ['Të dhënat publikohen si të hapura.', 'Data is published as open data.'],
  /* login modal */
  login_t: ['Hyrje për stafin', 'Staff sign-in'],
  login_b: ['Paneli i operimit është për operatorët e rrjetit: konfigurim nyjesh dhe raporte.', 'The operations console is for network operators: node configuration and reports.'],
  login_go: ['Vazhdo te paneli', 'Continue to console'], cancel: ['Anulo', 'Cancel'],
  email: ['E-mail', 'Email'], username: ['Përdoruesi', 'Username'], password: ['Fjalëkalimi', 'Password'],
  login_err: ['Përdoruesi ose fjalëkalimi janë të gabuar.', 'Incorrect username or password.'],
  demo_note: ['Llogaritë e operatorëve krijohen nga administratori.', 'Operator accounts are created by an administrator.']
};
var CITY_EN = { 'Tiranë': 'Tirana', 'Korçë': 'Korça', 'Elbasan': 'Elbasan' };
var LANG_KEY = 'smartcity.lang';
A.lang = (function () { try { return global.localStorage.getItem(LANG_KEY) || 'sq'; } catch (e) { return 'sq'; } })();
A.setLang = function (l) { A.lang = (l === 'en' ? 'en' : 'sq'); try { global.localStorage.setItem(LANG_KEY, A.lang); } catch (e) {} };
A.t = function (k) { var e = DICT[k]; return e ? (A.lang === 'en' ? e[1] : e[0]) : k; };
A.cityName = function (c) { return A.lang === 'en' ? (CITY_EN[c] || c) : c; };

/* English strings for parameters + calendar */
var PARAM_EN = {
  pm25: { label: 'PM2.5', long: 'Fine particulate PM2.5', unit: 'µg/m³',
    desc: 'Particles under 2.5 µm that reach deep into the lungs and enter the bloodstream.', note: 'WHO daily limit: 15 µg/m³.' },
  pm10: { label: 'PM10', long: 'Coarse particulate PM10', unit: 'µg/m³',
    desc: 'Dust from traffic, construction and wood burning.', note: 'WHO daily limit: 45 µg/m³.' },
  tmp: { label: 'Temperature', long: 'Air temperature', unit: '°C',
    desc: 'Air temperature measured at node height.', note: 'Some nodes report 0.0 as a failed-sensor sentinel.' },
  hum: { label: 'Humidity', long: 'Relative humidity', unit: '%',
    desc: 'Relative humidity - drives how long particles stay suspended.', note: 'Dry below 30% · comfort 40–60% · high above 70%.' },
  snd: { label: 'Noise', long: 'Noise level (raw)', unit: '% of scale',
    desc: 'Raw microphone signal normalised to the sensor scale. Not dB - the sensors are not acoustically calibrated.', note: 'Raw→% conversion per node; no validated dB formula.' },
  uv: { label: 'UV', long: 'UV radiation (raw)', unit: '% of scale',
    desc: 'Raw UV photodiode output normalised to the sensor scale. Not the UV Index - that needs calibration.', note: 'Values ≥98% indicate a saturated or blocked sensor.' },
  pres: { label: 'Pressure', long: 'Atmospheric pressure', unit: 'hPa',
    desc: 'Reported only by Raspberry Pi nodes with a BMP sensor.', note: 'LoRaWAN nodes do not report this field.' },
  rain: { label: 'Rain', long: 'Rain sensor (raw)', unit: 'raw',
    desc: 'Analogue rain-sensor output. No mm/h calibration.', note: 'Not published - calibration missing.' }
};
A.tp = function (p, field) {
  if (!p) return '';
  if (A.lang === 'en' && PARAM_EN[p.key] && PARAM_EN[p.key][field] != null) return PARAM_EN[p.key][field];
  return p[field] || '';
};

var MON_EN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
var DAY_EN = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
var DAY_EN_S = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
var DAY_SQ_S = ['Die', 'Hën', 'Mar', 'Mër', 'Enj', 'Pre', 'Sht'];
A.fmtDateL = function (t) {
  var d = new Date(t);
  return A.lang === 'en' ? (MON_EN[d.getUTCMonth()] + ' ' + d.getUTCDate()) : A.fmtDate(t);
};
A.fmtDayShort = function (t) { var d = new Date(t); return (A.lang === 'en' ? DAY_EN_S : DAY_SQ_S)[d.getUTCDay()]; };
A.fmtDayNameL = function (t) { return A.lang === 'en' ? DAY_EN[new Date(t).getUTCDay()] : A.fmtDayName(t); };
A.fmtDateTimeL = function (t) { return A.fmtDateL(t) + ' ' + new Date(t).getUTCFullYear() + ', ' + A.fmtTime(t); };
A.fmtAgeL = function (ms) {
  if (A.lang !== 'en') return A.fmtAge(ms);
  if (ms == null || !isFinite(ms)) return '-';
  var s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return s + ' sec';
  var m = Math.round(s / 60); if (m < 60) return m + ' min';
  var h = Math.floor(m / 60); if (h < 48) return h + ' h' + (m % 60 ? ' ' + (m % 60) + ' min' : '');
  var d = Math.floor(h / 24); if (d < 60) return d + ' days';
  return Math.floor(d / 30) + ' months';
};

/* ------------------------------------------------- per-node configuration --
   Coverage radius, transport technology, ingest webhook and the per-node
   parameter set (a node may carry one sensor more than its neighbour).      */
var TECHS = {
  lorawan: { id: 'lorawan', label: ['LoRaWAN', 'LoRaWAN'], icon: 'solar:wi-fi-router-linear', hint: ['Nyje Arduino/Dragino përmes gateway-t LoRa', 'Arduino/Dragino node via a LoRa gateway'] },
  rpi_api: { id: 'rpi_api', label: ['Raspberry Pi - API', 'Raspberry Pi - API'], icon: 'solar:cpu-bolt-linear', hint: ['Raspberry Pi që poston direkt në endpoint HTTP', 'Raspberry Pi posting straight to an HTTP endpoint'] }
};
A.TECHS = TECHS;
A.techLabel = function (id) { var x = TECHS[id]; return x ? (A.lang === 'en' ? x.label[1] : x.label[0]) : id; };

var DEFAULT_PARAM_COLOR = { pm25: '#E07E2E', pm10: '#C2843A', tmp: '#B1322F', hum: '#4976F4', snd: '#6D28D9', uv: '#F79009', pres: '#1F8A4C', rain: '#38BDF8' };

function ensureParamDefaults(p) { if (p.color == null) p.color = DEFAULT_PARAM_COLOR[p.key] || '#08514A'; return p; }
A.config.params.forEach(ensureParamDefaults);
A.DEFAULT_PARAMS.forEach(ensureParamDefaults);
A.DEFAULT_PARAM_COLOR = DEFAULT_PARAM_COLOR;

function ensureNodeDefaults(n) {
  if (n.coverageM == null) n.coverageM = 150;
  if (n.tech == null) n.tech = /lora/i.test(n.transport || '') ? 'lorawan' : 'rpi_api';
  if (n.webhook == null) n.webhook = 'https://api.smartcitypollution.al/v1/ingest/' + (n.apiId || n.id);
  if (!n.params) {
    n.params = {};
    (n.sensors || []).forEach(function (k) { n.params[k] = { on: true, color: null }; });
  }
  return n;
}
A.config.nodes.forEach(ensureNodeDefaults);
A.DEFAULT_NODES.forEach(ensureNodeDefaults);
A.ensureNodeDefaults = ensureNodeDefaults;

/* Parameters this node actually publishes, in configured order. */
A.nodeParams = function (node, onlyPublic) {
  return A.config.params.filter(function (p) {
    if (onlyPublic && !p.public) return false;
    if ((node.sensors || []).indexOf(p.key) < 0) return false;
    var cfg = node.params && node.params[p.key];
    return !cfg || cfg.on !== false;
  });
};
A.paramColor = function (p, node) {
  var cfg = node && node.params && node.params[p.key];
  return (cfg && cfg.color) || p.color || '#08514A';
};
A.cities = function () {
  var seen = [], out = [];
  A.config.nodes.forEach(function (n) { if (n.city && seen.indexOf(n.city) < 0) { seen.push(n.city); out.push(n.city); } });
  return out;
};
A.nextNodeId = function () {
  var max = 0;
  A.config.nodes.forEach(function (n) { var m = /(\d+)$/.exec(n.id); if (m) max = Math.max(max, +m[1]); });
  return 'ND-' + String(max + 1).padStart(2, '0');
};

/* ---------------------------------------------------------- aggregation ----
   One entry point for every chart in both portals.
   mode: 'day'   → 24 hourly points ending at t
         'week'  → 7 daily means
         'month' → 30 daily means
   nodeIds of length > 1 are averaged (that is what "city" means here).      */
var MODES = {
  day:   { points: 24, label: ['Dita', 'Day'],   sub: ['24 orët e fundit', 'Last 24 hours'] },
  week:  { points: 7,  label: ['Java', 'Week'],  sub: ['7 ditët e fundit', 'Last 7 days'] },
  month: { points: 30, label: ['Muaji', 'Month'], sub: ['30 ditët e fundit', 'Last 30 days'] }
};
A.MODES = MODES;
A.modeLabel = function (m) { var x = MODES[m] || MODES.day; return A.lang === 'en' ? x.label[1] : x.label[0]; };
A.modeSub = function (m) { var x = MODES[m] || MODES.day; return A.lang === 'en' ? x.sub[1] : x.sub[0]; };

function dayKey(t) { return new Date(t).toISOString().slice(0, 10); }

A.trend = function (nodeIds, paramKey, mode, t) {
  t = t == null ? A.clock.t : t;
  var p = A.paramByKey(paramKey);
  var nodes = (nodeIds || []).map(A.nodeById).filter(Boolean).filter(function (n) { return (n.sensors || []).indexOf(paramKey) >= 0; });
  var out = { param: p, mode: mode, points: [], min: null, max: null, avg: null, nodes: nodes, valid: 0 };
  if (!p || !nodes.length) return out;

  if (mode === 'day') {
    var per = nodes.map(function (n) { return A.source().history(n, paramKey, t, 24); });
    for (var i = 0; i < 24; i++) {
      var vs = [];
      per.forEach(function (h) { if (h[i] && h[i].v != null) vs.push(h[i].v); });
      var tt = per[0][i] ? per[0][i].t : t - (23 - i) * HOUR;
      out.points.push({ t: tt, v: vs.length ? vs.reduce(function (a, b) { return a + b; }, 0) / vs.length : null,
        label: A.fmtTime(tt), full: A.fmtDateTimeL(tt) });
    }
  } else {
    var n_ = MODES[mode] ? MODES[mode].points : 7;
    var end = dayKey(t), map = {};
    nodes.forEach(function (n) {
      A.source().daily(n, paramKey).forEach(function (d) {
        if (d.day > end || d.v == null) return;
        (map[d.day] = map[d.day] || []).push(d.v);
      });
    });
    var keys = Object.keys(map).sort().slice(-n_);
    /* keep the calendar contiguous so gaps read as gaps, not as compression */
    if (keys.length) {
      var first = Date.parse(keys[0] + 'T00:00:00Z'), last = Date.parse(end + 'T00:00:00Z');
      var span = Math.min(n_, Math.round((last - first) / DAY) + 1);
      for (var k = span - 1; k >= 0; k--) {
        var dt = last - k * DAY, key = dayKey(dt), vs2 = map[key];
        out.points.push({ t: dt, v: vs2 ? vs2.reduce(function (a, b) { return a + b; }, 0) / vs2.length : null,
          label: mode === 'week' ? A.fmtDayShort(dt) : A.fmtDateL(dt), full: A.fmtDateL(dt) });
      }
    }
  }
  var vals = out.points.filter(function (d) { return d.v != null; }).map(function (d) { return d.v; });
  out.valid = vals.length;
  if (vals.length) {
    out.min = Math.min.apply(null, vals); out.max = Math.max.apply(null, vals);
    out.avg = vals.reduce(function (a, b) { return a + b; }, 0) / vals.length;
    out.last = vals[vals.length - 1];
    var half = Math.floor(vals.length / 2) || 1;
    var a1 = vals.slice(0, half).reduce(function (a, b) { return a + b; }, 0) / half;
    var a2 = vals.slice(-half).reduce(function (a, b) { return a + b; }, 0) / half;
    out.delta = a2 - a1;
  }
  return out;
};

/* ------------------------------------------------------------- reporting -- */
A.nodeStats = function (node) {
  var m = A.source().meta(node) || {};
  var nulls = m.nulls || {}, valid = m.valid || {};
  var params = A.nodeParams(node).map(function (p) {
    var v = valid[p.field] || 0, nl = nulls[p.field] || 0, tot = v + nl;
    return { key: p.key, label: A.tp(p, 'label'), valid: v, nulls: nl, total: tot,
      coverage: tot ? v / tot : 0, color: A.paramColor(p, node) };
  });
  var expected = 0;
  if (m.first && m.last && node.intervalS) expected = Math.round((A.parseTs(m.last) - A.parseTs(m.first)) / 1000 / node.intervalS);
  return {
    rows: m.n || 0, first: m.first || null, last: m.last || null,
    avgIntervalS: m.avgIntervalS || node.intervalS, rejoins: m.rejoins || 0,
    gaps1h: m.gaps1h || 0, maxGapH: m.maxGapH || 0,
    days: (m.days || []).length, expected: expected,
    completeness: expected ? Math.min(1, (m.n || 0) / expected) : null,
    params: params
  };
};
A.networkStats = function () {
  var out = { rows: 0, nodes: 0, active: 0, cities: A.cities().length, first: null, last: null };
  A.config.nodes.forEach(function (n) {
    var s = A.nodeStats(n);
    out.rows += s.rows; out.nodes++; if (n.active) out.active++;
    if (s.first && (!out.first || s.first < out.first)) out.first = s.first;
    if (s.last && (!out.last || s.last > out.last)) out.last = s.last;
  });
  return out;
};

/* --------------------------------------------------------- health advice --
   Audience-aware guidance derived from the live values of one city.        */
var ADVICE = {
  all: {
    label: ['Të gjithë', 'Everyone'], icon: 'solar:users-group-rounded-linear',
    txt: [
      ['Ajri është i pastër. Ditë e mirë për të qëndruar jashtë.', 'Air is clean. A good day to be outdoors.'],
      ['Cilësi e pranueshme. Nuk nevojitet asnjë masë e veçantë.', 'Acceptable quality. No special precautions needed.'],
      ['Kufizo qëndrimin e gjatë jashtë pranë rrugëve me trafik.', 'Limit long stays outdoors near busy roads.'],
      ['Shmang aktivitetin e gjatë jashtë. Mbyll dritaret nga rruga.', 'Avoid prolonged outdoor activity. Keep street-side windows closed.'],
      ['Qëndro brenda sa më shumë të jetë e mundur.', 'Stay indoors as much as possible.']
    ]
  },
  kids: {
    label: ['Fëmijë', 'Children'], icon: 'solar:balloon-linear',
    txt: [
      ['Lojë e lirë jashtë, pa kufizime.', 'Free outdoor play, no restrictions.'],
      ['Lojë jashtë është në rregull; preferoni parqet ndaj rrugëve.', 'Outdoor play is fine; prefer parks over roadsides.'],
      ['Shkurtoni kohën e lojës jashtë, sidomos në orët e trafikut.', 'Shorten outdoor play, especially at rush hour.'],
      ['Aktivitetet e shkollës jashtë duhen shtyrë.', 'Outdoor school activities should be postponed.'],
      ['Mbani fëmijët brenda dhe filtroni ajrin nëse mundeni.', 'Keep children indoors and filter the air if you can.']
    ]
  },
  old: {
    label: ['Të moshuar', 'Older adults'], icon: 'solar:user-heart-linear',
    txt: [
      ['Shëtitje e sigurt në çdo orë të ditës.', 'Walking is safe at any time of day.'],
      ['Ecja e zakonshme është e sigurt.', 'Your usual walk is safe.'],
      ['Zgjidhni orët e mëngjesit herët për shëtitjen.', 'Choose early morning for your walk.'],
      ['Shtyni shëtitjen; kontrolloni simptomat kardiake.', 'Postpone the walk; watch for cardiac symptoms.'],
      ['Mos dilni. Kontaktoni mjekun nëse ndiheni keq.', 'Do not go out. Contact your doctor if unwell.']
    ]
  },
  sport: {
    label: ['Sportistë', 'Athletes'], icon: 'solar:running-linear',
    txt: [
      ['Stërvitje intensive jashtë pa kufizime.', 'Intense outdoor training without limits.'],
      ['Stërvitja jashtë është në rregull.', 'Outdoor training is fine.'],
      ['Ulni intensitetin ose kaloni brenda.', 'Lower the intensity or move indoors.'],
      ['Stërvituni brenda - frymëmarrja e thellë shumëfishon ekspozimin.', 'Train indoors - deep breathing multiplies exposure.'],
      ['Anuloni stërvitjen jashtë.', 'Cancel outdoor training.']
    ]
  },
  asthma: {
    label: ['Astmatikë', 'Asthma & COPD'], icon: 'solar:jar-of-pills-linear',
    txt: [
      ['Pa rrezik shtesë sot.', 'No added risk today.'],
      ['Mbani inhalatorin me vete si zakonisht.', 'Carry your inhaler as usual.'],
      ['Mbani inhalatorin pranë; shmangni rrugët kryesore.', 'Keep your inhaler close; avoid main roads.'],
      ['Rrezik i lartë krizash. Qëndroni brenda dhe përdorni terapinë parandaluese.', 'High risk of attacks. Stay indoors and use preventive therapy.'],
      ['Rrezik shumë i lartë. Ndiqni planin e emergjencës.', 'Very high risk. Follow your emergency plan.']
    ]
  }
};
A.ADVICE = ADVICE;
A.adviceFor = function (aud, lvl) {
  var a = ADVICE[aud] || ADVICE.all;
  var i = Math.max(0, Math.min(4, lvl == null ? 1 : lvl));
  return { label: A.lang === 'en' ? a.label[1] : a.label[0], icon: a.icon,
    text: A.lang === 'en' ? a.txt[i][1] : a.txt[i][0] };
};

/* ---------------------------------------------------- label translation --
   air-core.js carries Albanian labels for AQI bands, grades, statuses and
   severities. One table translates whatever any of them returns.          */
var LABEL_EN = {
  'I mirë': 'Good', 'I moderuar': 'Moderate', 'I ndjeshëm': 'Unhealthy for sensitive groups',
  'I dëmshëm': 'Unhealthy', 'Rrezik': 'Hazardous',
  'Normal': 'Normal', 'I ulët': 'Low', 'Kujdes': 'Caution', 'Kritik': 'Critical',
  'Pa të dhëna': 'No data', 'Online': 'Online', 'Me vonesë': 'Delayed', 'Offline': 'Offline',
  'Jashtë shërbimi': 'Out of service', 'Në mirëmbajtje': 'Under maintenance',
  'Informacion': 'Info'
};
A.L = function (s) { return (A.lang === 'en' && LABEL_EN[s]) ? LABEL_EN[s] : s; };

A.persist();
})(window);
