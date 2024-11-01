# crypto_signals/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class CryptoSignalsConfig(AppConfig):
    name = 'crypto_signals'

    def ready(self):
        # Подключаем функцию к сигналу post_migrate
        post_migrate.connect(start_background_tasks, sender=self)

def start_background_tasks(sender, **kwargs):
    from background_task.models import Task
    from .tasks import collect_and_send_signals

    # Проверка, запущена ли уже задача
    if not Task.objects.filter(task_name='crypto_signals.tasks.collect_and_send_signals').exists():
        # Запускаем задачу с повторением каждые 60 секунд
        collect_and_send_signals(repeat=60)
