from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('user', 'User'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar_url = models.CharField(
        max_length=500,
        blank=True,
        default='https://api.dicebear.com/7.x/bottts/svg?seed=John'
    )
    job_title = models.CharField(max_length=100, blank=True, default='Administrator')

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        full_name = self.get_full_name()
        if full_name:
            return full_name
        return self.username
