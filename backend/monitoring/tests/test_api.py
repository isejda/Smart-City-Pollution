"""API tests against the DRF endpoints (uses a temporary PostgreSQL test DB)."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APITestCase

from monitoring.models import Node, Reading, Settings


class ApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # config only (fast); then a handful of readings around the cursor for ND-01
        call_command('seed_data', '--no-readings', verbosity=0)
        cls.settings = Settings.load()
        cls.t = cls.settings.cursor
        node = Node.objects.get(node_id='ND-01')
        for k in range(6):
            Reading.objects.create(
                node=node, ts=cls.t - k * timedelta(hours=1),
                pm25=18.0 - k, pm10=30.0, tmp=24.0, hum=55.0, snd=360.0, uv=500.0, rain=5.0,
            )
        cls.operator = get_user_model().objects.create_user(username='tester-operator', password='irrelevant')

    def setUp(self):
        # Settings writes are operator-only (JWT-authenticated);
        # parameters/cities/nodes/readings/snapshot/dataset stay public for the anonymous client.
        self.client.force_authenticate(user=self.operator)

    def test_parameters_list(self):
        r = self.client.get('/api/parameters/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['count'], 8)

    def test_cities_and_nodes(self):
        self.assertEqual(self.client.get('/api/cities/').data['count'], 3)
        nodes = self.client.get('/api/nodes/').data
        self.assertEqual(nodes['count'], 6)

    def test_nodes_public_filter(self):
        r = self.client.get('/api/nodes/?public=true')
        self.assertEqual(r.data['count'], 6)

    def test_node_latest(self):
        r = self.client.get('/api/nodes/ND-01/latest/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['status'], 'online')       # reading exists at cursor
        self.assertEqual(r.data['values']['pm25'], 18.0)
        self.assertTrue(r.data['usable'])

    def test_node_history(self):
        r = self.client.get('/api/nodes/ND-01/history/?param=pm25&hours=6')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['param'], 'pm25')
        self.assertTrue(len(r.data['points']) >= 5)

    def test_snapshot(self):
        r = self.client.get('/api/snapshot/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data['nodes']), 6)
        self.assertTrue(any(c['name'] == 'Tiranë' for c in r.data['cities']))

    def test_network_stats(self):
        r = self.client.get('/api/network-stats/')
        self.assertEqual(r.data['nodes'], 6)
        self.assertTrue(r.data['rows'] >= 6)

    def test_dataset_endpoint_shape(self):
        """The engine-shaped dataset the front-ends hydrate from."""
        r = self.client.get('/api/dataset/')
        self.assertEqual(r.status_code, 200)
        d = r.data
        self.assertIn('nodes', d)
        self.assertTrue(d['rows'] >= 6)
        # ND-01 has the readings created in setUpTestData
        series = d['nodes'].get('A8404172C75D105A')
        self.assertIsNotNone(series)
        for key in ('h0Ms', 'hours', 'daily', 'days', 'diurnal', 'tail', 'valid', 'nulls'):
            self.assertIn(key, series)
        self.assertIn('pm25', series['hours'])
        self.assertEqual(len(series['diurnal']['pm25']), 24)

    def test_settings_get_and_patch(self):
        r = self.client.get('/api/settings/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['source'], 'dataset')
        r2 = self.client.patch('/api/settings/', {'replay_speed': 120}, format='json')
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(Settings.load().replay_speed, 120)
