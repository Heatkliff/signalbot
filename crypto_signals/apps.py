# crypto_signals/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class CryptoSignalsConfig(AppConfig):
    name = 'crypto_signals'

