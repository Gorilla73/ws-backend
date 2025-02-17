import re
from rest_framework import serializers

def validate_password(value):
    # Проверка сложности пароля: должен содержать минимум 8 символов, хотя бы одну букву и одну цифру
    if len(value) < 8:
        raise serializers.ValidationError("Пароль должен содержать как минимум 8 символов.")
    if not re.search(r'[A-Za-z]', value):
        raise serializers.ValidationError("Пароль должен содержать хотя бы одну букву.")
    if not re.search(r'\d', value):
        raise serializers.ValidationError("Пароль должен содержать хотя бы одну цифру.")