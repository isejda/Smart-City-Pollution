"""REST API for the Smart City Pollution backend."""
import logging
import threading
from datetime import timedelta

from django.conf import settings as django_settings
from django.core.management import call_command
from django.db import IntegrityError
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import Max, Min, Count
from rest_framework import mixins, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveUpdateAPIView

from . import services
from .dataset import build_dataset
from .models import Parameter, City, Node, Reading, Settings
from .serializers import (
    ParameterSerializer, CitySerializer, NodeSerializer, ReadingSerializer,
    ReadingIngestSerializer, SettingsSerializer,
)

logger = logging.getLogger(__name__)

# generate_forecast deletes and rebuilds the whole Forecast table (monitoring/management/
# commands/generate_forecast.py); two overlapping runs would race on that delete+recreate.
# A single lock, held for the duration of one run, keeps auto-triggered regenerations
# serialized; a trigger that arrives while one is already running is simply dropped, since
# the run in flight (or the next packet) will cover it.
_forecast_regen_lock = threading.Lock()


def _trigger_forecast_regeneration():
    """Fire-and-forget: rerun generate_forecast in the background after a live packet is
    stored, so the AI forecast reflects it without waiting for a container restart."""
    if not _forecast_regen_lock.acquire(blocking=False):
        logger.info('generate_forecast already running - skipping this trigger.')
        return

    def _run():
        try:
            call_command('generate_forecast')
        except Exception:
            logger.exception('Auto-triggered generate_forecast failed.')
        finally:
            _forecast_regen_lock.release()

    threading.Thread(target=_run, daemon=True, name='forecast-regen').start()


class HasDeviceKey(permissions.BasePermission):
    """A physical node authenticates with a shared secret in X-Device-Key, not JWT -
    hardware cannot do an interactive login/refresh flow the way a staff browser can."""

    def has_permission(self, request, view):
        key = request.headers.get('X-Device-Key', '')
        return bool(key) and key == django_settings.DEVICE_INGEST_KEY

HOUR = timedelta(hours=1)


# --------------------------------------------------------------------------- helpers
def resolve_time(request, settings=None):
    """Target replay time: ?t=ISO, else settings.cursor, else now."""
    raw = request.query_params.get('t')
    if raw:
        dt = parse_datetime(raw.replace(' ', 'T'))
        if dt:
            return dt if timezone.is_aware(dt) else timezone.make_aware(dt, timezone.utc)
    settings = settings or Settings.load()
    return settings.cursor or timezone.now()


def params_by_key():
    return {p.key: p for p in Parameter.objects.all()}


def latest_reading(node, t):
    return node.readings.filter(ts__lte=t).order_by('-ts').first()


# ------------------------------------------------------------------------ viewsets
class ParameterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    lookup_field = 'key'
    filterset_fields = ['public']
    permission_classes = [permissions.AllowAny]


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    lookup_field = 'name'
    permission_classes = [permissions.AllowAny]


class NodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Node.objects.select_related('city').all()
    serializer_class = NodeSerializer
    lookup_field = 'node_id'
    filterset_fields = ['public', 'active', 'city__name', 'tech', 'maintenance']
    search_fields = ['name', 'eui', 'node_id', 'address']
    permission_classes = [permissions.AllowAny]

    @action(detail=True)
    def latest(self, request, node_id=None):
        """Latest snapshot for one node at the target time."""
        node = self.get_object()
        settings = Settings.load()
        t = resolve_time(request, settings)
        snap = services.node_snapshot(node, latest_reading(node, t), t, params_by_key(), settings)
        snap['status_meta'] = services.STATUS.get(snap['status'])
        return Response(snap)

    @action(detail=True)
    def history(self, request, node_id=None):
        """Hourly calibrated history: ?param=pm25&hours=24[&t=]."""
        node = self.get_object()
        key = request.query_params.get('param', 'pm25')
        hours = int(request.query_params.get('hours', 24))
        p = Parameter.objects.filter(key=key).first()
        if p is None:
            return Response({'detail': f'unknown parameter {key}'}, status=400)
        t = resolve_time(request)
        start = t - hours * HOUR
        rows = node.readings.filter(ts__gt=start, ts__lte=t).order_by('ts')
        points = []
        for r in rows:
            raw = getattr(r, key, None)
            points.append({'t': r.ts, 'v': services.calibrate(node, key, raw) if raw is not None else None})
        return Response({'node': node.node_id, 'param': key, 'unit': p.unit, 'points': points})

    @action(detail=True)
    def daily(self, request, node_id=None):
        """Per-day mean (calibrated) for a parameter over the node's history."""
        node = self.get_object()
        key = request.query_params.get('param', 'pm25')
        p = Parameter.objects.filter(key=key).first()
        if p is None:
            return Response({'detail': f'unknown parameter {key}'}, status=400)
        buckets = {}
        for r in node.readings.filter(**{f'{key}__isnull': False}).order_by('ts').values_list('ts', key):
            ts, raw = r
            day = ts.date().isoformat()
            buckets.setdefault(day, []).append(services.calibrate(node, key, raw))
        days = [{'day': d, 'v': round(sum(v) / len(v), 3)} for d, v in sorted(buckets.items())]
        return Response({'node': node.node_id, 'param': key, 'unit': p.unit, 'days': days})

    @action(detail=True)
    def stats(self, request, node_id=None):
        """Dataset volume + coverage stats for one node (feeds the reports view)."""
        node = self.get_object()
        agg = node.readings.aggregate(n=Count('id'), first=Min('ts'), last=Max('ts'))
        span_s = (agg['last'] - agg['first']).total_seconds() if agg['first'] and agg['last'] else 0
        expected = round(span_s / node.interval_s) if node.interval_s else 0
        return Response({
            'node': node.node_id, 'rows': agg['n'], 'first': agg['first'], 'last': agg['last'],
            'interval_s': node.interval_s, 'days': node.readings.dates('ts', 'day').count(),
            'expected': expected,
            'completeness': round(min(1.0, agg['n'] / expected), 4) if expected else None,
        })


class ReadingViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """GET is public (read the network's history); POST is a live packet from a
    physical node and requires the device key (HasDeviceKey), not staff JWT."""
    queryset = Reading.objects.select_related('node').all()
    serializer_class = ReadingSerializer
    filterset_fields = ['node__node_id']
    ordering_fields = ['ts']
    ordering = ['-ts']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReadingIngestSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action == 'create':
            return [HasDeviceKey()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            # Same node + timestamp already stored (device retry/duplicate delivery) -
            # not an error from the device's point of view, just a no-op.
            raise ValidationError({'detail': 'A reading for this node at this timestamp already exists.'})
        _trigger_forecast_regeneration()

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get('from'):
            dt = parse_datetime(p['from'].replace(' ', 'T'))
            if dt:
                qs = qs.filter(ts__gte=dt)
        if p.get('to'):
            dt = parse_datetime(p['to'].replace(' ', 'T'))
            if dt:
                qs = qs.filter(ts__lte=dt)
        return qs


class SettingsView(RetrieveUpdateAPIView):
    serializer_class = SettingsSerializer

    def get_object(self):
        return Settings.load()


# ---------------------------------------------------------------------- plain views
class SnapshotView(APIView):
    """Full network snapshot at the target time (mirrors Air.snapshot)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        settings = Settings.load()
        t = resolve_time(request, settings)
        pbk = params_by_key()
        nodes = list(Node.objects.all())
        # one latest reading per node (<= t)
        snaps = []
        for n in nodes:
            snaps.append(services.node_snapshot(n, latest_reading(n, t), t, pbk, settings))
        # per-city rollup of public, usable nodes
        cities = {}
        by_id = {s['node_id']: s for s in snaps}
        for n in nodes:
            if not n.public:
                continue
            c = cities.setdefault(n.city.name, {'name': n.city.name, 'nodes': 0, 'live': 0})
            c['nodes'] += 1
            if by_id[n.node_id]['usable']:
                c['live'] += 1
        return Response({'t': t, 'nodes': snaps, 'cities': list(cities.values())})


class DatasetView(APIView):
    """The full replay dataset in the front-end engine's AIR_DATASET shape.
    The Vue web app and the React Native app hydrate the engine from this,
    making PostgreSQL the single source of truth for measurement data."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(build_dataset())


class NetworkStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        agg = Reading.objects.aggregate(rows=Count('id'), first=Min('ts'), last=Max('ts'))
        return Response({
            'rows': agg['rows'] or 0,
            'nodes': Node.objects.count(),
            'active': Node.objects.filter(active=True).count(),
            'public': Node.objects.filter(public=True).count(),
            'cities': City.objects.count(),
            'params': Parameter.objects.count(),
            'first': agg['first'],
            'last': agg['last'],
        })
