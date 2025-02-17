from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, views, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from userApi.models import CustomUser
from userApi.serializers import ProfileSerializer, MyTokenObtainPairSerializer, RegisterSerializer


# Login User
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# Register User
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# Profile Detail and Update

class ProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendConfirmationEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.confirm_email:
            return Response({"message": "Email уже подтвержден"}, status=status.HTTP_400_BAD_REQUEST)

        user.send_confirmation_email()
        return Response({"message": "Письмо с подтверждением отправлено"}, status=status.HTTP_200_OK)


class ConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, confirmation_key):
        user = get_object_or_404(CustomUser, confirmation_key=confirmation_key)
        user.confirm_email = True
        user.confirmation_key = None
        user.save()

        return Response({"message": "Email успешно подтвержден"}, status=status.HTTP_200_OK)