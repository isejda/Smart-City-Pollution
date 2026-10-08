from django.contrib import admin

from .models import Parameter, City, Node, Reading, Forecast, Settings


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('key', 'label', 'unit', 'public', 'normal', 'warn', 'crit')
    list_filter = ('public',)
    ordering = ('sort',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en', 'lat', 'lng')


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'name', 'city', 'tech', 'active', 'public', 'maintenance', 'interval_s')
    list_filter = ('city', 'tech', 'active', 'public', 'maintenance')
    search_fields = ('node_id', 'name', 'eui', 'address')


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ('node', 'ts', 'pm25', 'pm10', 'tmp', 'hum')
    list_filter = ('node',)
    date_hierarchy = 'ts'


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('node', 'target', 'ts', 'horizon_hour', 'prediction', 'model_name', 'origin')
    list_filter = ('node', 'target', 'model_name')
    date_hierarchy = 'ts'


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('source', 'replay', 'replay_speed', 'cursor')
