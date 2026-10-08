"""
Build the replay dataset in the exact shape the front-end `Air` engine consumes
(`window.AIR_DATASET`), straight from the database. This lets the Vue web app and
the React Native app hydrate from PostgreSQL instead of their bundled synthetic
data, while the engine and every view stay byte-for-byte the same.

Shape (per node, keyed by EUI):
    { h0Ms, hours{field:[raw|null]}, daily{field:[mean|null]}, days[],
      diurnal{field:[24]}, tail[{t, field:raw}], n, first, last,
      avgIntervalS, rejoins, gaps1h, maxGapH, nulls{field:N}, valid{field:N} }

Values are RAW (the engine calibrates on read), matching the bundled dataset.
"""
from collections import defaultdict

from django.db.models import Max

from . import services
from .models import Forecast, Node

FIELDS = ['pm25', 'pm10', 'tmp', 'hum', 'snd', 'uv', 'pres', 'rain']
HOUR_S = 3600


def _fmt_wall(dt):
    """Naive 'YYYY-MM-DD HH:MM:SS' (UTC wall-clock), matching parseTs() on the client."""
    return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None


def _ms(dt):
    return int(dt.timestamp() * 1000)


def _forecast_block(node):
    """AI forecast for one node, keyed by Parameter field (80% band as lo/hi -
    matches the shape chart.js already draws via chartSVG's o.forecast)."""
    rows = list(node.forecasts.order_by('ts').values(
        'target', 'ts', 'prediction', 'lower_80', 'upper_80', 'model_name', 'origin', 'source_data_cutoff',
    ))
    if not rows:
        return None, None
    forecast = defaultdict(list)
    models = {}
    origin = cutoff = None
    for r in rows:
        field = services.FIELD_FOR_TARGET.get(r['target'])
        if field is None:
            continue
        forecast[field].append({
            't': _ms(r['ts']), 'v': r['prediction'], 'lo': r['lower_80'], 'hi': r['upper_80'],
        })
        models[field] = r['model_name']
        origin, cutoff = r['origin'], r['source_data_cutoff']
    if not forecast:
        return None, None
    meta = {'origin': _fmt_wall(origin), 'sourceCutoff': _fmt_wall(cutoff), 'models': models}
    return dict(forecast), meta


def build_node_series(node):
    rows = list(node.readings.order_by('ts').values('ts', *FIELDS))
    if not rows:
        return None

    fields = [f for f in FIELDS if f in node.sensors]
    first_ts = rows[0]['ts']
    last_ts = rows[-1]['ts']
    h0 = first_ts
    length = int((last_ts - first_ts).total_seconds() // HOUR_S) + 1

    hours = {f: [None] * length for f in fields}
    nulls = {f: 0 for f in fields}
    valid = {f: 0 for f in fields}
    present = [False] * length

    for r in rows:
        idx = int(round((r['ts'] - h0).total_seconds() / HOUR_S))
        if idx < 0 or idx >= length:
            continue
        present[idx] = True
        for f in fields:
            v = r[f]
            if v is None:
                nulls[f] += 1
            else:
                hours[f][idx] = v
                valid[f] += 1

    # comms gaps (whole missing hours)
    gaps1h = max_gap = cur_gap = rejoins = 0
    was_null = True
    for ok in present:
        if not ok:
            gaps1h += 1
            cur_gap += 1
            max_gap = max(max_gap, cur_gap)
            was_null = True
        else:
            if was_null:
                rejoins += 1
            was_null = False
            cur_gap = 0

    # daily means + ordered day list
    day_order = []
    dsum = defaultdict(lambda: defaultdict(float))
    dcnt = defaultdict(lambda: defaultdict(int))
    for r in rows:
        dk = r['ts'].date().isoformat()
        if dk not in dcnt:
            day_order.append(dk)
        for f in fields:
            if r[f] is not None:
                dsum[dk][f] += r[f]
                dcnt[dk][f] += 1
    daily = {f: [(round(dsum[d][f] / dcnt[d][f], 3) if dcnt[d][f] else None) for d in day_order] for f in fields}

    # diurnal profile (mean by hour-of-day)
    hsum = {f: [0.0] * 24 for f in fields}
    hcnt = {f: [0] * 24 for f in fields}
    for r in rows:
        hod = r['ts'].hour
        for f in fields:
            if r[f] is not None:
                hsum[f][hod] += r[f]
                hcnt[f][hod] += 1
    diurnal = {f: [(round(hsum[f][h] / hcnt[f][h], 3) if hcnt[f][h] else None) for h in range(24)] for f in fields}

    # recent packet tail
    tail = []
    for r in rows[-48:]:
        rec = {'t': _ms(r['ts'])}
        any_val = False
        for f in fields:
            if r[f] is not None:
                rec[f] = r[f]
                any_val = True
        if any_val:
            tail.append(rec)

    forecast, forecast_meta = _forecast_block(node)

    return {
        'h0Ms': _ms(h0),
        'hours': hours,
        'daily': daily,
        'days': day_order,
        'diurnal': diurnal,
        'tail': tail,
        'n': len(rows),
        'first': _fmt_wall(first_ts),
        'last': _fmt_wall(last_ts),
        'avgIntervalS': node.interval_s,
        'rejoins': rejoins,
        'gaps1h': gaps1h,
        'maxGapH': max_gap,
        'nulls': nulls,
        'valid': valid,
        'forecast': forecast,
        'forecastMeta': forecast_meta,
    }


def build_dataset():
    nodes_out = {}
    total_rows = 0
    overall_first = None
    overall_last = None

    for node in Node.objects.all():
        series = build_node_series(node)
        if series is None:
            continue
        nodes_out[node.eui] = series
        total_rows += series['n']
        first = node.readings.order_by('ts').values_list('ts', flat=True).first()
        last = node.readings.order_by('-ts').values_list('ts', flat=True).first()
        if first and (overall_first is None or first < overall_first):
            overall_first = first
        if last and (overall_last is None or last > overall_last):
            overall_last = last

    # When an AI forecast has been generated, its source_data_cutoff is a
    # better default "now" than the loosest last-reading across every node:
    # some nodes may still hold synthetic data that runs a few hours past the
    # real import the forecast was actually computed from (see air-core.js,
    # which opens the replay clock on this value when present).
    forecast_cutoff = Forecast.objects.aggregate(v=Max('source_data_cutoff'))['v']

    return {
        'source': 'PostgreSQL · Django REST API',
        'rows': total_rows,
        'first': _fmt_wall(overall_first),
        'last': _fmt_wall(overall_last),
        'forecastCutoff': _fmt_wall(forecast_cutoff),
        'nodes': nodes_out,
    }
