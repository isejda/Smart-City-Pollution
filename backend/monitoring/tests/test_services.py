"""Pure unit tests for the ported domain logic (no database needed)."""
from datetime import datetime, timezone
from types import SimpleNamespace

from django.test import SimpleTestCase

from monitoring import services
from monitoring.models import Parameter, Node, Settings


class CalibrationTests(SimpleTestCase):
    def test_snd_raw_to_percent_of_scale(self):
        node = Node(node_id='X', scale={'snd': 255, 'uv': 255})
        self.assertAlmostEqual(services.calibrate(node, 'snd', 127.5), 50.0, places=3)

    def test_uv_raw_to_percent(self):
        node = Node(node_id='X', scale={'uv': 1023})
        self.assertAlmostEqual(services.calibrate(node, 'uv', 1023), 100.0, places=3)

    def test_pm_is_passthrough(self):
        node = Node(node_id='X', scale={})
        self.assertEqual(services.calibrate(node, 'pm25', 18.0), 18.0)

    def test_none_stays_none(self):
        node = Node(node_id='X', scale={})
        self.assertIsNone(services.calibrate(node, 'pm25', None))


class GradeTests(SimpleTestCase):
    def setUp(self):
        self.p = Parameter(key='pm25', normal=15, warn=25, crit=50)

    def test_bands(self):
        self.assertEqual(services.grade(self.p, 10)['key'], 'normal')
        self.assertEqual(services.grade(self.p, 20)['key'], 'moderate')
        self.assertEqual(services.grade(self.p, 30)['key'], 'warning')
        self.assertEqual(services.grade(self.p, 60)['key'], 'critical')
        self.assertEqual(services.grade(self.p, None)['key'], 'nodata')

    def test_low_warn(self):
        p = Parameter(key='tmp', normal=30, warn=35, crit=40, low_warn=0)
        self.assertEqual(services.grade(p, -2)['key'], 'low')


class AqiTests(SimpleTestCase):
    def test_bands(self):
        self.assertEqual(services.aqi_from_pm25(6)['lvl'], 0)
        self.assertEqual(services.aqi_from_pm25(16.5)['label'], 'I moderuar')
        self.assertEqual(services.aqi_from_pm25(60)['lvl'], 3)
        self.assertIsNone(services.aqi_from_pm25(None)['v'])


class StatusTests(SimpleTestCase):
    def setUp(self):
        self.settings = Settings(online_mult=2, delayed_mult=6, validity_min=180)

    def test_status_progression(self):
        node = Node(node_id='X', active=True, maintenance=False, interval_s=100)
        self.assertEqual(services.status_of(node, 0, self.settings), 'online')
        self.assertEqual(services.status_of(node, 100_000, self.settings), 'online')      # 100s <= 200s
        self.assertEqual(services.status_of(node, 400_000, self.settings), 'delayed')     # <= 600s
        self.assertEqual(services.status_of(node, 900_000, self.settings), 'offline')
        self.assertEqual(services.status_of(node, None, self.settings), 'nodata')

    def test_inactive_and_maintenance(self):
        self.assertEqual(services.status_of(Node(active=False), 0, self.settings), 'inactive')
        self.assertEqual(services.status_of(Node(active=True, maintenance=True), 0, self.settings), 'maintenance')


class SnapshotTests(SimpleTestCase):
    def test_node_snapshot(self):
        t = datetime(2026, 5, 29, 13, 0, tzinfo=timezone.utc)
        node = Node(node_id='ND-X', active=True, maintenance=False, interval_s=100,
                    sensors=['pm25', 'snd'], scale={'snd': 1023})
        pbk = {
            'pm25': Parameter(key='pm25', field='pm25', phys_min=0, phys_max=1000, dec=1, normal=15, warn=25, crit=50),
            'snd': Parameter(key='snd', field='snd', phys_min=0, phys_max=100, dec=0, normal=35, warn=55, crit=75),
        }
        settings = Settings(online_mult=2, delayed_mult=6, validity_min=180)
        reading = SimpleNamespace(ts=t, pm25=18.0, snd=511.5)
        snap = services.node_snapshot(node, reading, t, pbk, settings)
        self.assertEqual(snap['status'], 'online')
        self.assertTrue(snap['usable'])
        self.assertAlmostEqual(snap['values']['snd'], 50.0, places=1)   # 511.5/1023*100
        self.assertEqual(snap['values']['pm25'], 18.0)
        # env_grade only escalates on warning/critical (matches the engine); a
        # "moderate" reading keeps the node's overall grade at normal.
        self.assertEqual(snap['env_grade'], 'normal')

    def test_snapshot_no_reading_is_nodata(self):
        t = datetime(2026, 5, 29, 13, 0, tzinfo=timezone.utc)
        node = Node(node_id='ND-Y', active=True, interval_s=100, sensors=['pm25'], scale={})
        pbk = {'pm25': Parameter(key='pm25', phys_min=0, phys_max=1000, normal=15, warn=25, crit=50)}
        settings = Settings(online_mult=2, delayed_mult=6, validity_min=180)
        snap = services.node_snapshot(node, None, t, pbk, settings)
        self.assertEqual(snap['status'], 'nodata')
        self.assertFalse(snap['usable'])
