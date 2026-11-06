from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import LogoutSerializer
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiResponse

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
    request=LogoutSerializer,
    responses={
        205: None,
        400: OpenApiResponse(
            description="Invalid or missing refresh token."
        )
    }
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (KeyError, TokenError):
            return Response(
                {"detail": "Invalid or missing refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)
