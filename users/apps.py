from django.apps import AppConfig
from django.urls import register_converter


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        from .id_encryption import EncryptedIdConverter
        register_converter(EncryptedIdConverter, 'eid')
