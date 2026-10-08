"""
Replace the synthetic readings of any node whose EUI matches a real device in
ml_forecast/data/sensor_hourly_clean.csv (the cleaned, hourly-resampled
history the forecasting model was trained on) with that real history, and
move the replay cursor to the real data's last timestamp so the app opens on
real, forecast-eligible data by default.

Nodes with no matching EUI (currently ND-06) keep their synthetic history.

Usage:
    python manage.py import_real_history
    python manage.py import_real_history --path /custom/sensor_hourly_clean.csv
    python manage.py import_real_history --keep-cursor
"""
import csv
from collections import defaultdict
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from monitoring.models import Node, Reading, Settings

DEFAULT_PATH = Path(__file__).resolve().parents[3] / 'ml_forecast' / 'data' / 'sensor_hourly_clean.csv'

# CSV column (ml_forecast target name) -> Reading field
FIELD_MAP = {
    'humidity_pct': 'hum',
    'pm10_ugm3': 'pm10',
    'pm25_ugm3': 'pm25',
    'pressure_hpa': 'pres',
    'rain_raw': 'rain',
    'sound_raw': 'snd',
    'temperature_c': 'tmp',
    'uv_raw': 'uv',
}


def parse_wall(s):
    """Parse a naive 'YYYY-MM-DD HH:MM:SS' wall-clock string as aware UTC (matches seed_data.py)."""
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=dt_timezone.utc)


class Command(BaseCommand):
    help = "Import the real cleaned hourly sensor history for nodes whose EUI matches it."

    def add_arguments(self, parser):
        parser.add_argument('--path', default=str(DEFAULT_PATH), help='Path to sensor_hourly_clean.csv')
        parser.add_argument(
            '--keep-cursor', action='store_true',
            help="Don't move Settings.cursor to the imported data's last timestamp.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        path = Path(opts['path'])
        if not path.is_file():
            raise CommandError(f'History file not found: {path}')

        nodes_by_eui = {n.eui: n for n in Node.objects.all()}
        rows_by_node_id = defaultdict(list)
        unmatched_euis = set()
        last_ts = None

        with path.open(newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                eui = row['sensor_id']
                node = nodes_by_eui.get(eui)
                if node is None:
                    unmatched_euis.add(eui)
                    continue
                ts = parse_wall(row['timestamp'])
                if last_ts is None or ts > last_ts:
                    last_ts = ts
                values = {
                    field: (float(row[csv_col]) if row.get(csv_col) not in (None, '') else None)
                    for csv_col, field in FIELD_MAP.items()
                }
                rows_by_node_id[node.node_id].append(Reading(node=node, ts=ts, **values))

        if not rows_by_node_id:
            raise CommandError(
                'No CSV rows matched any Node.eui - check --path and the sensor_id values in the CSV.'
            )

        matched_node_ids = sorted(rows_by_node_id)
        deleted_count, _ = Reading.objects.filter(node__node_id__in=matched_node_ids).delete()

        objs = [reading for rows in rows_by_node_id.values() for reading in rows]
        Reading.objects.bulk_create(objs, batch_size=2000)

        if not opts['keep_cursor'] and last_ts is not None:
            settings = Settings.load()
            settings.cursor = last_ts
            settings.save()

        self.stdout.write(self.style.SUCCESS(
            f'Imported {len(objs)} real readings for {len(matched_node_ids)} node(s): {matched_node_ids} '
            f'(replaced {deleted_count} synthetic rows).'
        ))
        if not opts['keep_cursor'] and last_ts is not None:
            self.stdout.write(f'Settings.cursor moved to {last_ts:%Y-%m-%d %H:%M:%S} UTC.')
        if unmatched_euis:
            self.stdout.write(self.style.WARNING(
                f'{len(unmatched_euis)} sensor_id(s) in the CSV had no matching Node.eui: {sorted(unmatched_euis)}'
            ))
        node_ids_kept_synthetic = sorted(
            n.node_id for n in Node.objects.all() if n.node_id not in rows_by_node_id
        )
        if node_ids_kept_synthetic:
            self.stdout.write(f'Kept synthetic data for: {node_ids_kept_synthetic}')
