"""
Domain models for the Smart City Pollution backend.

These mirror the front-end `Air` engine's data model (parameters, nodes, hourly
readings and settings) so the API can serve the same shapes the Vue web app and
the React Native app already consume.
"""
from django.db import models


class Parameter(models.Model):
    """A measured quantity (PM2.5, temperature, …) with its thresholds & display."""
    key = models.SlugField(primary_key=True, max_length=16)          # 'pm25'
    field = models.CharField(max_length=16)                          # dataset field name
    label = models.CharField(max_length=64)
    long = models.CharField(max_length=128, blank=True)
    unit = models.CharField(max_length=24, blank=True)
    icon = models.CharField(max_length=64, blank=True)
    dec = models.PositiveSmallIntegerField(default=1)                # decimals for display
    public = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    phys_min = models.FloatField(default=0)
    phys_max = models.FloatField(default=1000)
    disp_min = models.FloatField(default=0)
    disp_max = models.FloatField(default=100)

    normal = models.FloatField(null=True, blank=True)
    warn = models.FloatField(null=True, blank=True)
    crit = models.FloatField(null=True, blank=True)
    low_warn = models.FloatField(null=True, blank=True)

    gradient = models.JSONField(default=list)                        # [[stop, '#hex'], …]
    color = models.CharField(max_length=9, default='#08514A')
    radius_m = models.PositiveIntegerField(default=4200)
    blur = models.FloatField(default=0.55)
    opacity = models.FloatField(default=0.72)
    note = models.TextField(blank=True)
    sort = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort', 'key']

    def __str__(self):
        return f'{self.label} ({self.key})'


class City(models.Model):
    name = models.CharField(max_length=64, unique=True)              # 'Tiranë'
    name_en = models.CharField(max_length=64, blank=True)
    lat = models.FloatField()
    lng = models.FloatField()

    class Meta:
        verbose_name_plural = 'cities'
        ordering = ['name']

    def __str__(self):
        return self.name


class Node(models.Model):
    """A physical sensor node."""
    TRANSPORT_LORA = 'LoRaWAN'
    node_id = models.CharField(max_length=16, unique=True)           # 'ND-01'
    eui = models.CharField(max_length=64, unique=True)
    join_eui = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=128)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='nodes')
    place = models.CharField(max_length=64, null=True, blank=True)
    address = models.CharField(max_length=200, blank=True)
    lat = models.FloatField()
    lng = models.FloatField()

    transport = models.CharField(max_length=32, blank=True)
    hw = models.CharField(max_length=64, blank=True)
    tech = models.CharField(max_length=16, default='rpi_api')        # 'lorawan' | 'rpi_api'
    installed_at = models.DateField(null=True, blank=True)
    interval_s = models.PositiveIntegerField(default=120)            # expected reporting interval

    active = models.BooleanField(default=True)
    public = models.BooleanField(default=True)
    maintenance = models.BooleanField(default=False)

    coverage_m = models.PositiveIntegerField(default=150)
    scale = models.JSONField(default=dict)                          # raw sensor scale per key
    sensors = models.JSONField(default=list)                        # parameter keys present
    api_id = models.CharField(max_length=64, blank=True)
    webhook = models.URLField(blank=True)
    tz = models.CharField(max_length=32, default='Europe/Tirane')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['node_id']

    def __str__(self):
        return f'{self.node_id} - {self.name}'


class Reading(models.Model):
    """One hourly packet of RAW sensor values for a node."""
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='readings')
    ts = models.DateTimeField()

    pm25 = models.FloatField(null=True, blank=True)
    pm10 = models.FloatField(null=True, blank=True)
    tmp = models.FloatField(null=True, blank=True)
    hum = models.FloatField(null=True, blank=True)
    snd = models.FloatField(null=True, blank=True)
    uv = models.FloatField(null=True, blank=True)
    pres = models.FloatField(null=True, blank=True)
    rain = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['node', 'ts']
        constraints = [
            models.UniqueConstraint(fields=['node', 'ts'], name='uniq_node_ts'),
        ]
        indexes = [
            models.Index(fields=['node', 'ts'], name='idx_reading_node_ts'),
            models.Index(fields=['ts'], name='idx_reading_ts'),
        ]

    def __str__(self):
        return f'{self.node.node_id} @ {self.ts:%Y-%m-%d %H:%M}'


class Forecast(models.Model):
    """One hourly point of a 72-hour AI forecast for one node/target.

    Rows come from the trained model bundle in ``ml_forecast/`` (see
    ``monitoring.management.commands.generate_forecast``); ``origin`` and
    ``ts`` are UTC wall-clock, matching ``Reading.ts``. ``target`` uses the
    model's own field names (e.g. 'pm25_ugm3'), not the shorter Parameter
    keys - see ``services.TARGET_FOR_FIELD``.
    """
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='forecasts')
    target = models.CharField(max_length=32)
    origin = models.DateTimeField()
    ts = models.DateTimeField()
    horizon_hour = models.PositiveSmallIntegerField()

    prediction = models.FloatField()
    lower_80 = models.FloatField()
    upper_80 = models.FloatField()
    lower_95 = models.FloatField()
    upper_95 = models.FloatField()

    model_name = models.CharField(max_length=64)
    unit = models.CharField(max_length=24, blank=True)
    source_data_cutoff = models.DateTimeField()
    recent_coverage = models.FloatField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['node', 'target', 'ts']
        constraints = [
            models.UniqueConstraint(fields=['node', 'target', 'origin', 'ts'], name='uniq_forecast_row'),
        ]
        indexes = [
            models.Index(fields=['node', 'target', 'ts'], name='idx_forecast_node_target_ts'),
        ]

    def __str__(self):
        return f'{self.node.node_id}/{self.target} +{self.horizon_hour}h @ {self.ts:%Y-%m-%d %H:%M}'


class Settings(models.Model):
    """Singleton runtime configuration (row id is forced to 1)."""
    tz = models.CharField(max_length=32, default='Europe/Tirane')
    online_mult = models.FloatField(default=2)
    delayed_mult = models.FloatField(default=6)
    validity_min = models.PositiveIntegerField(default=180)
    source = models.CharField(max_length=16, default='dataset')
    rest_base = models.CharField(max_length=200, default='https://api.airmonitor.al/v1')
    ws_url = models.CharField(max_length=200, default='wss://api.airmonitor.al/v1/stream')
    poll_s = models.PositiveIntegerField(default=30)
    replay = models.BooleanField(default=True)
    replay_speed = models.PositiveIntegerField(default=75)
    cursor = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Runtime settings'
