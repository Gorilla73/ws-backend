from sqlite3 import IntegrityError

from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.translation import gettext_lazy as _

from .validators import validate_password

from userApi.models import CustomUser


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['email'] = user.email

        return token

    def validate(self, attrs):
        try:
            # Пытаемся выполнить стандартную валидацию
            data = super().validate(attrs)
        except exceptions.AuthenticationFailed:
            # Если аутентификация не удалась, возвращаем ошибку на русском
            raise exceptions.AuthenticationFailed(
                _('Неверный логин или пароль.')
            )
        except exceptions.ValidationError:
            # Если данные не прошли валидацию, возвращаем ошибку на русском
            raise exceptions.ValidationError(
                _('Пожалуйста, введите корректные данные.')
            )

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=CustomUser.objects.all(), message="Этот email уже используется.")]
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2',)

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        try:
            user = CustomUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
        except IntegrityError:
            raise serializers.ValidationError({"email": "Этот email уже используется."})

        return user


class ProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'is_staff', 'is_active', 'saved_statistic']

    def validate(self, attrs):
        if 'password' in attrs and 'password2' in attrs:
            if attrs['password'] != attrs['password2']:
                raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
            validated_data.pop('password2', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
