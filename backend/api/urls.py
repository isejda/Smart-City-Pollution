from django.urls import path

from .views import LoginView, RefreshView, RegisterView, health

urlpatterns = [
    path("health/", health, name="health"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("login/refresh/", RefreshView.as_view(), name="login_refresh"),
]
