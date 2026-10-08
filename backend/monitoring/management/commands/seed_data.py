"""
Seed the database with the full domain configuration and realistic dummy data:
parameters, cities, nodes, runtime settings, and a synthetic hourly readings
history for every node (same generator as the front-end dataset).

Usage:
    python manage.py seed_data            # idempotent upsert of config + data
    python manage.py seed_data --flush    # wipe monitoring tables first
    python manage.py seed_data --no-readings   # config only (fast)
"""
import math
import os
import random
from datetime import datetime, timedelta, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from monitoring import defaults
from monitoring.models import Parameter, City, Node, Reading, Settings

HOUR = timedelta(hours=1)


def parse_wall(s):
    """Parse a naive 'YYYY-MM-DD HH:MM:SS' wall-clock string as aware UTC."""
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=dt_timezone.utc)


def bell(hod, c, w):
    dx = min(abs(hod - c), 24 - abs(hod - c))
    return math.exp(-(dx * dx) / (2 * w * w))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class Command(BaseCommand):
    help = 'Seed the database with domain config and synthetic readings.'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete existing monitoring data first.')
        parser.add_argument('--no-readings', action='store_true', help='Skip generating the readings history.')

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts['flush']:
            self.stdout.write('Flushing monitoring tables…')
            for m in (Reading, Node, Parameter, City, Settings):
                m.objects.all().delete()

        self._seed_config()
        self._seed_superuser()
        if not opts['no_readings']:
            self._seed_readings()
        self.stdout.write(self.style.SUCCESS('Seed complete.'))
        self.stdout.write(
            f'  cities={City.objects.count()} parameters={Parameter.objects.count()} '
            f'nodes={Node.objects.count()} readings={Reading.objects.count()}'
        )

    # --------------------------------------------------------------- superuser
    def _seed_superuser(self):
        """Upsert the superadmin from DJANGO_SUPERUSER_* env vars. The password is
        reset on every seed so the documented credentials always work."""
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        user, _ = get_user_model().objects.get_or_create(username=username)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

    # ------------------------------------------------------------------ config
    def _seed_config(self):
        for c in defaults.CITIES:
            City.objects.update_or_create(name=c['name'], defaults=c)
        for p in defaults.PARAMETERS:
            Parameter.objects.update_or_create(key=p['key'], defaults=p)
        cities = {c.name: c for c in City.objects.all()}
        for n in defaults.NODES:
            data = dict(n)
            data['city'] = cities[n['city']]
            Node.objects.update_or_create(node_id=n['node_id'], defaults=data)
        s = dict(defaults.SETTINGS)
        s['cursor'] = parse_wall(s['cursor'])
        Settings.objects.update_or_create(pk=1, defaults=s)
        self.stdout.write('  config seeded (cities, parameters, nodes, settings)')

    # ---------------------------------------------------------------- readings
    def _seed_readings(self):
        Reading.objects.all().delete()
        h0 = parse_wall(defaults.GLOBAL_FIRST)
        h_end = parse_wall(defaults.GLOBAL_LAST)
        total_span = (h_end - h0).total_seconds()
        nodes = {n.node_id: n for n in Node.objects.all()}
        batch, made = [], 0

        for node_id, (start_s, end_s, cfg) in defaults.NODE_WINDOWS.items():
            node = nodes[node_id]
            start, end = parse_wall(start_s), parse_wall(end_s)
            scale = node.scale or {}
            fields = list(node.sensors)
            rng = {f: random.Random(f'{node_id}|{f}') for f in fields}
            i0 = int((start - h0).total_seconds() // 3600)
            i1 = int((end - h0).total_seconds() // 3600)

            for i in range(i0, i1 + 1):
                t = h0 + i * HOUR
                hod = t.hour
                prog = (t - h0).total_seconds() / total_span
                row = {}
                for f in fields:
                    r = rng[f]
                    v = None
                    if f == 'pm25':
                        diur = 1 + 0.45 * bell(hod, 8, 3) + 0.55 * bell(hod, 20, 3)
                        seas = 1 - 0.45 * prog
                        v = cfg['pm'] * diur * seas * (0.75 + r.random() * 0.5)
                        if r.random() < 0.02:
                            v += 20 + r.random() * 30
                        v = clamp(v, 0.1, 90)
                        if cfg.get('null_pm') and r.random() < cfg['null_pm']:
                            v = None
                    elif f == 'pm10':
                        base10 = (cfg['pm'] * 1.7 + 6) * (1 - 0.4 * prog)
                        v = base10 * (0.7 + r.random() * 0.6) + 4
                        if cfg.get('pm10_spike') and r.random() < 0.004:
                            v = 1000 + r.random() * 900
                        v = clamp(v, 1, 2000)
                    elif f == 'tmp':
                        season_t = 7 + 18 * prog
                        diur_t = -5 * math.cos((hod - 3) / 24 * 2 * math.pi)
                        v = season_t + diur_t + (r.random() - 0.5) * 3
                        v = clamp(v, -3, 44)
                        if cfg.get('tmp_sentinel') and r.random() < cfg['tmp_sentinel']:
                            v = 0
                    elif f == 'hum':
                        if cfg.get('hum_low') is not None:
                            v = cfg['hum_low'] + (r.random() - 0.5) * 6
                        else:
                            base_h = 62 - 22 * bell(hod, 15, 5)
                            v = base_h + (r.random() - 0.5) * 14 - 8 * prog
                        v = clamp(v, 3, 98)
                    elif f == 'snd':
                        sc = scale.get('snd', 255)
                        diur_s = 0.32 + 0.22 * bell(hod, 9, 4) + 0.2 * bell(hod, 19, 4) - 0.12 * bell(hod, 3, 3)
                        v = sc * diur_s * (0.8 + r.random() * 0.4)
                        v = clamp(v, 0, sc)
                    elif f == 'uv':
                        sc = scale.get('uv', 255)
                        if cfg.get('uv_stuck'):
                            v = sc * 0.975 + (r.random() - 0.5) * 8
                        else:
                            day = bell(hod, 13, 3.2)
                            v = sc * (0.05 + 0.85 * day * (0.8 + 0.4 * prog)) * (0.85 + r.random() * 0.3)
                        v = clamp(v, 0, sc)
                    elif f == 'pres':
                        v = cfg.get('pres_base', 1013) + math.sin(i / 40) * 6 + (r.random() - 0.5) * 4
                        v = clamp(v, 850, 1080)
                    elif f == 'rain':
                        sc = scale.get('rain', 255)
                        v = (r.random() * sc * 0.6) if r.random() < 0.15 else (r.random() * sc * 0.05)
                        v = clamp(v, 0, sc)

                    if v is not None and r.random() < 0.012:
                        v = None
                    row[f] = None if v is None else round(v, 3)

                batch.append(Reading(node=node, ts=t, **row))
                if len(batch) >= 2000:
                    Reading.objects.bulk_create(batch)
                    made += len(batch)
                    batch = []
        if batch:
            Reading.objects.bulk_create(batch)
            made += len(batch)
        self.stdout.write(f'  readings generated: {made}')
