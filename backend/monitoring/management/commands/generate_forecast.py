"""
Run the trained forecasting model (ml_forecast/) against the current Reading
history and store the resulting 72-hour forecast in the Forecast table.

The model only produces rows for sensor/target pairs that pass its own
freshness + coverage gate (see the technical report, "Active-series
gating") - most nodes/targets will simply be absent from the output, which
is expected, not an error.

Usage:
    python manage.py generate_forecast
"""
import csv
import sys
import tempfile
from datetime import timezone as dt_timezone
from pathlib import Path

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from monitoring.models import Forecast, Node, Reading

BACKEND_ROOT = Path(django_settings.BASE_DIR)
MODEL_PATH = BACKEND_ROOT / 'ml_forecast' / 'artifacts' / 'environmental_forecasting_model.joblib'

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _aware(pandas_ts):
    """pandas.Timestamp (naive, UTC wall-clock) -> aware python datetime (matches Reading.ts)."""
    return pandas_ts.to_pydatetime().replace(tzinfo=dt_timezone.utc)


class Command(BaseCommand):
    help = 'Regenerate the 72-hour AI forecast from the current reading history.'

    def handle(self, *args, **opts):
        from ml_forecast.src.modeling import load_verified_bundle, predict_from_loaded_bundle
        from ml_forecast.src.preprocessing import prepare_data

        if not Reading.objects.exists():
            raise CommandError('No readings in the database - run seed_data / import_real_history first.')

        self.stdout.write(f'Loading verified model bundle from {MODEL_PATH.name}...')
        bundle = load_verified_bundle(MODEL_PATH)
        config = bundle['config']

        with tempfile.TemporaryDirectory(prefix='forecast-') as tmp_dir:
            tmp = Path(tmp_dir)
            source_csv = tmp / 'source.csv'
            row_count = self._export_source_csv(config, source_csv)
            self.stdout.write(f'Exported {row_count} readings across {Node.objects.count()} node(s).')

            prepared = prepare_data(source_csv, config)
            forecast_df = predict_from_loaded_bundle(
                bundle, prepared, tmp / 'forecast.csv', tmp / 'eligibility.csv'
            )

        if forecast_df.empty:
            self.stdout.write(self.style.WARNING(
                'No sensor/target pair is currently eligible (fresh enough + covered enough) - '
                'no forecast rows generated. Nothing was overwritten.'
            ))
            return

        nodes_by_eui = {n.eui: n for n in Node.objects.all()}
        objs, skipped_euis = [], set()
        for row in forecast_df.itertuples(index=False):
            node = nodes_by_eui.get(str(row.sensor_id))
            if node is None:
                skipped_euis.add(row.sensor_id)
                continue
            objs.append(Forecast(
                node=node,
                target=row.target,
                origin=_aware(row.origin),
                ts=_aware(row.timestamp),
                horizon_hour=int(row.horizon_hour),
                prediction=float(row.prediction),
                lower_80=float(row.lower_80),
                upper_80=float(row.upper_80),
                lower_95=float(row.lower_95),
                upper_95=float(row.upper_95),
                model_name=row.model_name,
                unit=row.unit,
                source_data_cutoff=_aware(row.source_data_cutoff),
                recent_coverage=float(row.recent_coverage),
            ))

        with transaction.atomic():
            Forecast.objects.all().delete()
            Forecast.objects.bulk_create(objs, batch_size=2000)

        targets = sorted({o.target for o in objs})
        by_node = sorted({o.node.node_id for o in objs})
        self.stdout.write(self.style.SUCCESS(
            f'Generated {len(objs)} forecast rows for {len(targets)} target(s) on {by_node}: {targets}'
        ))
        if skipped_euis:
            self.stdout.write(self.style.WARNING(
                f'{len(skipped_euis)} forecasted sensor_id(s) had no matching Node: {sorted(skipped_euis)}'
            ))

    @staticmethod
    def _export_source_csv(config, out_path):
        """Reading + Node -> the model's 16-column raw source schema."""
        columns = list(config['data']['source_columns'])
        rows = (
            Reading.objects.select_related('node')
            .order_by('ts')
            .values_list(
                'node__eui', 'node__place', 'node__name', 'ts',
                'hum', 'pm10', 'pm25', 'pres', 'rain', 'snd', 'tmp', 'uv',
            )
        )
        count = 0
        with out_path.open('w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for i, (eui, place, name, ts, hum, pm10, pm25, pres, rain, snd, tmp, uv) in enumerate(rows, start=1):
                writer.writerow({
                    'id': i,
                    'indoor_lora_dev_eui': eui,
                    'indoor_lora_join_eui': '',
                    'indoor_lora_dev_adr': '',
                    'place': place or '',
                    'description': name or '',
                    'altitude_m': '',
                    'humidity_pct': '' if hum is None else hum,
                    'pm10_ugm3': '' if pm10 is None else pm10,
                    'pm25_ugm3': '' if pm25 is None else pm25,
                    'pressure_hpa': '' if pres is None else pres,
                    'rain_raw': '' if rain is None else rain,
                    'sound_raw': '' if snd is None else snd,
                    'temperature_c': '' if tmp is None else tmp,
                    'uv_raw': '' if uv is None else uv,
                    'created_at': ts.strftime('%Y-%m-%d %H:%M:%S'),
                })
                count = i
        return count
