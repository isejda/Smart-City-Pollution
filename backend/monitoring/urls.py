from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('parameters', views.ParameterViewSet)
router.register('cities', views.CityViewSet)
router.register('nodes', views.NodeViewSet)
router.register('readings', views.ReadingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('snapshot/', views.SnapshotView.as_view(), name='snapshot'),
    path('dataset/', views.DatasetView.as_view(), name='dataset'),
    path('network-stats/', views.NetworkStatsView.as_view(), name='network-stats'),
]
