"""
Domain logic ported from the front-end `Air` engine: calibration, validity
checks, environmental grading, the air-quality index, colour ramps, node status
and snapshot building. Kept dependency-free so it is trivially unit-testable.
"""
from datetime import timedelta

MIN_MS = 60_000
HOUR = timedelta(hours=1)


# --------------------------------------------------------------------- calibration
def calibrate(node, param_key, raw, scale=None):
    """RAW sensor value -> calibrated value (matches air-core.js calibrate())."""
    if raw is None:
        return None
    v = raw
    scale = scale if scale is not None else (node.scale or {})
    if param_key in ('snd', 'uv') and scale.get(param_key):
        v = raw / scale[param_key] * 100.0        # raw -> % of sensor scale
    # 'rain' keeps its raw value; pm/tmp/hum/pres are used as-is
    return round(v * 1000) / 1000


def validity(param, value, raw):
    """Return a reason string when a value must NOT be treated as a measurement."""
    if value is None:
        return 'null'
    if value < param.phys_min or value > param.phys_max:
        return 'jashtë intervalit fizik'
    if param.key in ('tmp', 'hum') and raw == 0:
        return 'vlerë sentinel 0.0'
    if param.key == 'uv' and value >= 98:
        return 'sensor i ngopur'
    return None


# ------------------------------------------------------------------------- grading
GRADE_NODATA = {'key': 'nodata', 'label': 'Pa të dhëna', 'fg': '#72767F', 'bg': '#F2F2F2'}


def grade(param, v):
    if v is None:
        return dict(GRADE_NODATA)
    if param.crit is not None and v >= param.crit:
        return {'key': 'critical', 'label': 'Kritik', 'fg': '#B1322F', 'bg': '#F7EDED'}
    if param.warn is not None and v >= param.warn:
        return {'key': 'warning', 'label': 'Kujdes', 'fg': '#9A5B00', 'bg': '#FEF6E7'}
    if param.low_warn is not None and v <= param.low_warn:
        return {'key': 'low', 'label': 'I ulët', 'fg': '#4976F4', 'bg': '#EAF0FE'}
    if param.normal is not None and v >= param.normal:
        return {'key': 'moderate', 'label': 'I moderuar', 'fg': '#C77A00', 'bg': '#FEF6E7'}
    return {'key': 'normal', 'label': 'Normal', 'fg': '#1F8A4C', 'bg': '#F0FDF4'}


# --------------------------------------------------------------------- air quality
_AQI_BANDS = [
    {'m': 50, 'c': '#1F8A4C', 'b': '#F0FDF4', 'l': 'I mirë', 'lt': '#4ADE80'},
    {'m': 100, 'c': '#C77A00', 'b': '#FEF6E7', 'l': 'I moderuar', 'lt': '#FBBF56'},
    {'m': 150, 'c': '#DA6A00', 'b': '#FDF0E4', 'l': 'I ndjeshëm', 'lt': '#FB9245'},
    {'m': 200, 'c': '#B1322F', 'b': '#F7EDED', 'l': 'I dëmshëm', 'lt': '#F87171'},
    {'m': 1e9, 'c': '#6D28D9', 'b': '#F1ECFB', 'l': 'Rrezik', 'lt': '#C4B5FD'},
]


def aqi_from_pm25(pm):
    if pm is None:
        return {'v': None, 'label': 'Pa të dhëna', 'lvl': -1, 'color': '#979797', 'bg': '#F2F2F2', 'light': '#B8BDC4'}
    if pm <= 12:
        a = pm / 12 * 50
    elif pm <= 35.4:
        a = 50 + (pm - 12) / 23.4 * 50
    elif pm <= 55.4:
        a = 100 + (pm - 35.4) / 20 * 50
    elif pm <= 150.4:
        a = 150 + (pm - 55.4) / 95 * 100
    else:
        a = min(500, 250 + (pm - 150.4) / 100 * 100)
    a = round(a)
    i = 0
    while a > _AQI_BANDS[i]['m']:
        i += 1
    band = _AQI_BANDS[i]
    return {'v': a, 'label': band['l'], 'lvl': i, 'color': band['c'], 'bg': band['b'], 'light': band['lt']}


# ---------------------------------------------------------------------- colour ramp
def _hex2rgb(h):
    return [int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)]


def ramp_color(param, t):
    g = param.gradient
    if not g:
        return [8, 81, 74]
    t = max(0.0, min(1.0, t))
    for i in range(1, len(g)):
        if t <= g[i][0]:
            a, b = g[i - 1], g[i]
            f = (t - a[0]) / ((b[0] - a[0]) or 1)
            ca, cb = _hex2rgb(a[1]), _hex2rgb(b[1])
            return [round(ca[k] + (cb[k] - ca[k]) * f) for k in range(3)]
    return _hex2rgb(g[-1][1])


def color_for(param, v):
    if v is None or param.disp_max == param.disp_min:
        return '#B8BDC4'
    norm = (v - param.disp_min) / (param.disp_max - param.disp_min)
    r, g, b = ramp_color(param, norm)
    return f'rgb({r},{g},{b})'


def fmt_val(param, v):
    if v is None:
        return '-'
    return f'{v:.{param.dec}f}' if param.dec else str(round(v))


# ---------------------------------------------------------------------------- status
def status_of(node, age_ms, settings):
    if not node.active:
        return 'inactive'
    if node.maintenance:
        return 'maintenance'
    if age_ms is None:
        return 'nodata'
    iv = node.interval_s * 1000
    if age_ms <= iv * settings.online_mult:
        return 'online'
    if age_ms <= iv * settings.delayed_mult:
        return 'delayed'
    return 'offline'


STATUS = {
    'online': {'label': 'Online', 'fg': '#1F8A4C', 'bg': '#F0FDF4', 'dot': '#22A65A'},
    'delayed': {'label': 'Me vonesë', 'fg': '#9A5B00', 'bg': '#FEF6E7', 'dot': '#F79009'},
    'offline': {'label': 'Offline', 'fg': '#B1322F', 'bg': '#F7EDED', 'dot': '#B1322F'},
    'nodata': {'label': 'Pa të dhëna', 'fg': '#72767F', 'bg': '#F2F2F2', 'dot': '#979797'},
    'inactive': {'label': 'Jashtë shërbimi', 'fg': '#72767F', 'bg': '#F2F2F2', 'dot': '#B8BDC4'},
    'maintenance': {'label': 'Në mirëmbajtje', 'fg': '#4976F4', 'bg': '#EAF0FE', 'dot': '#4976F4'},
}

SEVERITY = {
    'info': {'label': 'Informacion', 'fg': '#4976F4', 'bg': '#EAF0FE', 'rank': 1},
    'warning': {'label': 'Kujdes', 'fg': '#9A5B00', 'bg': '#FEF6E7', 'rank': 2},
    'critical': {'label': 'Kritik', 'fg': '#B1322F', 'bg': '#F7EDED', 'rank': 3},
}

PARAM_FIELDS = ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'pres', 'rain']

# Parameter.key (this app) <-> the trained model's own target field names
# (ml_forecast/config/model_config.yaml -> data.targets). Rain/sound/UV stay
# raw ADC-like signals on both sides, so no unit conversion is involved.
TARGET_FOR_FIELD = {
    'hum': 'humidity_pct',
    'pm10': 'pm10_ugm3',
    'pm25': 'pm25_ugm3',
    'pres': 'pressure_hpa',
    'rain': 'rain_raw',
    'snd': 'sound_raw',
    'tmp': 'temperature_c',
    'uv': 'uv_raw',
}
FIELD_FOR_TARGET = {v: k for k, v in TARGET_FOR_FIELD.items()}


# -------------------------------------------------------------------- node snapshot
def node_snapshot(node, reading, t, params_by_key, settings):
    """Build a snapshot dict for one node at time t, given its latest reading (<= t)."""
    age_ms = None
    packet_at = None
    if reading is not None:
        packet_at = reading.ts
        age_ms = max(0.0, (t - reading.ts).total_seconds() * 1000)

    status = status_of(node, age_ms, settings)
    values, raw, invalid, missing = {}, {}, {}, []
    for key in node.sensors:
        p = params_by_key.get(key)
        if p is None:
            continue
        r = getattr(reading, key, None) if reading is not None else None
        raw[key] = r
        if r is None:
            values[key] = None
            missing.append(key)
            continue
        v = calibrate(node, key, r)
        values[key] = v
        reason = validity(p, v, r)
        if reason:
            invalid[key] = reason

    fresh = age_ms is not None and age_ms <= settings.validity_min * MIN_MS
    usable = status in ('online', 'delayed') and fresh

    worst, sensors, ok = 'normal', 0, 0
    for key in node.sensors:
        p = params_by_key.get(key)
        if p is None:
            continue
        sensors += 1
        v = values.get(key)
        if v is not None and key not in invalid:
            ok += 1
            g = grade(p, v)
            if g['key'] == 'critical':
                worst = 'critical'
            elif g['key'] == 'warning' and worst != 'critical':
                worst = 'warning'
    quality = (ok / sensors) if sensors else 0.0
    env_grade = worst if usable else 'nodata'

    return {
        'node_id': node.node_id,
        't': t,
        'packet_at': packet_at,
        'age_ms': age_ms,
        'status': status,
        'values': values,
        'raw': raw,
        'invalid': invalid,
        'missing': missing,
        'fresh': fresh,
        'usable': usable,
        'quality': round(quality, 4),
        'env_grade': env_grade,
    }
