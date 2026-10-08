# The `Air` engine

This folder holds the **domain engine** that powers both the web app and the
mobile app. It is plain, framework-agnostic JavaScript with no build step and no
dependencies (Leaflet is only needed for the optional heatmap layer). It attaches
everything to a single global, **`window.Air`**.

The same three files are shipped in `mobile/src/engine/` and run there under
Hermes via a small shim - see [Running under React Native](#running-under-react-native).

> **Why keep the original engine instead of rewriting it in Vue/React?**
> The engine already encodes every domain rule (thresholds, calibration, node
> status, forecasting, AQI, gradients, the replay clock). Rewriting it per
> framework would only introduce divergence and bugs. Keeping it
> framework-agnostic is what lets the public site, the operator console and
> the phone all agree on every number.

---

## Files & load order

Load order matters and is the same on both clients:

```
air-dataset.js   → sets window.AIR_DATASET (the replay data)
air-core.js      → reads AIR_DATASET, builds window.Air
air-extra.js     → patches window.Air (i18n, analytics, advice, reporting)
```

- **`air-dataset.js`** - a synthetic, deterministic replay dataset (the original
  design shipped this file empty). It builds hourly series, daily means, diurnal
  profiles, packet tails and validity stats for all nodes. See the root
  [README → The dataset](../../README.md#the-dataset).
- **`air-core.js`** - the core:
  - **Config store**: `DEFAULT_PARAMS`, `DEFAULT_NODES`, `DEFAULT_SETTINGS`,
    merged with anything saved in `localStorage`.
  - **Data adapter** (`Air.source()`): `readAt`, `history`, `daily`, `diurnal`,
    `meta`, `packets`. A `dataset` source (replay) and a stub `rest` source are
    provided; implement the REST/WS source to go live.
  - **Calibration & validity**: raw→calibrated conversion and "is this a real
    measurement?" checks.
  - **Status + snapshot**: `statusOf`, `snapshot(t)` (a full picture of every node
    at time `t`).
  - **Forecasting**: `forecast(...)`, `bestWindow`, `dayOutlook`.
  - **AQI, gradients, formatting**, and an **IDW heatmap layer** for Leaflet.
  - The **replay clock** (`Air.clock`).
- **`air-extra.js`** - the bilingual layer (SQ/EN `DICT`), parameter/label
  translations, the trend aggregator `Air.trend(...)`, reporting (`nodeStats`,
  `networkStats`), and the **health-advice** tables.

---

## The data model

**Parameter** (`Air.config.params[]`): `key`, `label`, `unit`, `icon`, `dec`,
`public`, thresholds `normal` / `warn` / `crit` / `lowWarn`,
`gradient`, `physMin/physMax`, `dispMin/dispMax`, `note`.

**Node** (`Air.config.nodes[]`): `id`, `eui`, `name`, `city`, `lat`, `lng`,
`active`, `public`, `maintenance`, `transport`, `hw`, `intervalS`, `installedAt`,
`sensors[]`, `coverageM`, `tech`, `webhook`.

**Snapshot** (`Air.snapshot(t)`): `{ t, nodes:[sn], byId:{id:sn}, cities:{…} }`.
Each `sn`: `{ node, status, ageMs, packetAt, values:{key:num|null}, raw, invalid,
usable, fresh, quality, envGrade, lastKnown }`.

---

## API cheat-sheet

Everything is on `Air`. The most-used members:

```js
// config
Air.config.params / nodes / settings
Air.paramByKey(key)   Air.nodeById(id)   Air.publicParams()   Air.cities()
Air.persist()         // save config edits to localStorage

// snapshots & aggregation
Air.snapshot(t?)                         // full picture at time t (defaults to clock)
Air.cityAvg(snap, city, key)   Air.netAvg(snap, key)   Air.heatPoints(snap, key)
Air.trend([nodeIds], key, 'day'|'week'|'month', t?)   // chart series + min/avg/max/delta

// status, grading, air quality
Air.statusOf(node, snap, t)   Air.STATUS[status]      // {label,icon,fg,bg,dot}
Air.grade(param, value)                                // {key,label,fg,bg}
Air.aqi(pm25)                                          // {v,label,lvl,color,bg,light}
Air.SEVERITY[sev]                                      // {label,fg,bg,icon,rank}

// forecasting
Air.forecast([nodeId], key, t?, leadH?)   Air.bestWindow(fc)   Air.dayOutlook(fc)

// colours & formatting
Air.colorFor(param, v)   Air.rampCss(param)   Air.paramColor(param, node)   Air.fmtVal(param, v)
Air.fmtTime · fmtDate · fmtDateTime · fmtDateTimeL · fmtAge · fmtAgeL · fmtDayShort

// i18n
Air.lang ('sq'|'en')   Air.setLang(l)   Air.t(key)   Air.cityName(c)   Air.tp(param, field)   Air.L(label)

// reporting
Air.nodeStats(node)   Air.networkStats()

// map layer (needs Leaflet)
Air.idwLayer(L, opts)   // → layer with .setPoints(Air.heatPoints(snap,key)) / .setOptions({param})

// replay clock
Air.clock.t                 // current replay time (ms)
Air.clock.play() / pause() / toggle() / set(ms)
Air.clock.on((t, kind) => …)   // kind: 'tick' | 'set' | 'state'
Air.source().range()        // { from, to } in ms
```

---

## The replay clock

The dataset is historical, so the app "plays" it back. `Air.clock` holds a virtual
time `t`, advances it by `settings.replaySpeed` dataset-seconds per real second when
playing, and notifies subscribers. Both reactive bridges subscribe to it: on each
tick they recompute `Air.snapshot()`.

- **Web** autostarts on the public portal; the operator console starts paused (its
  header play button controls it).
- **Mobile** autostarts on launch (`mobile/App.js`).

---

## Reactive bridges

The engine is not reactive by itself. Each client adds a thin adapter that turns
clock ticks into UI updates:

| | file | exposes |
|---|---|---|
| Web | `src/composables/useAir.js` | `Air`, reactive `snap`, `lang`, `tick`, `playing`, `play/pause/toggle/seek`, `setLang`, `t` |
| Mobile | `mobile/src/hooks/useAir.js` | the same surface as a React hook |

Both keep a single shared snapshot and re-render subscribers on each tick, so
components just read `snap` and derive from it.

---

## Running under React Native

The engine was written for browsers (it references `window`, `document` and
`localStorage`). Under Hermes those don't exist, so `mobile/src/engine/shim.js`
provides minimal versions **before** the engine loads:

- `global.window = global` (so the IIFEs' `})(window)` resolves),
- a stub `global.document` (only `currentScript` / `createElement` / `head` are
  touched, inside `try/catch`), and
- a synchronous in-memory `global.localStorage`.

`mobile/src/engine/index.js` imports the shim first, then the three engine files in
order, and exports `Air`. This is verified: the engine boots under these shims in a
plain Node runtime and produces the same dataset, snapshots, trends and forecasts
as the browser.

> The mobile `localStorage` shim is session-scoped (in memory). Wire it to
> `@react-native-async-storage/async-storage` if you want operator/config edits to
> persist across app launches.

---

## Persistence

Config edits (parameter thresholds, node fields, settings) are written through a
single `store` object in `air-core.js`, keyed in `localStorage` as
**`airmonitor.demo.v3`**. Swapping in a real backend means replacing that one
object - nothing in the views changes.
