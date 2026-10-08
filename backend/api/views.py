from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Public - anyone can create an account."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """Public - exchanges username/password for a JWT pair."""

    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
    """Public - exchanges a refresh token for a new access token."""

    permission_classes = [permissions.AllowAny]


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({"status": "ok"})
