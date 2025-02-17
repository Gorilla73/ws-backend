from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import Group, Permission

from django.core.mail import send_mail
from django.conf import settings
import uuid


class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email=email, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    # groups = baseModels.ManyToManyField(Group, verbose_name='Groups', blank=True, related_name='customuser_set')
    # user_permissions = baseModels.ManyToManyField(Permission, verbose_name='User permissions', blank=True,
    #                                           related_name='customuser_set')

    # user_id = baseModels.AutoField(primary_key=True)
    email = models.EmailField(max_length=50, unique=True, verbose_name='email')
    confirmation_key = models.CharField(max_length=32, blank=True, null=True, verbose_name='Ключ подтверждения email')
    confirm_email = models.BooleanField(default=False, verbose_name='Подтверждение email')
    username = models.CharField(max_length=50, verbose_name='Никнейм')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    saved_statistic = models.JSONField(default=dict)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', ]

    objects = CustomUserManager()

    def __str__(self):
        return self.username

