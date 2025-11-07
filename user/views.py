from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		serializer = RegisterSerializer(data=request.data)
		if serializer.is_valid():
			user = serializer.save()
			return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
	# uses SimpleJWT's TokenObtainPairView
	permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request):
		"""Blacklist the provided refresh token to logout user."""
		refresh_token = request.data.get('refresh')
		if not refresh_token:
			return Response({'detail': 'refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			token = RefreshToken(refresh_token)
			token.blacklist()
			return Response(status=status.HTTP_205_RESET_CONTENT)
		except Exception as e:
			return Response({'detail': 'invalid token'}, status=status.HTTP_400_BAD_REQUEST)
