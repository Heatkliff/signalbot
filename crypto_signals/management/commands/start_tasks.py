from django.core.management.base import BaseCommand
from background_task.models import Task
from crypto_signals.tasks import collect_and_send_signals

class Command(BaseCommand):
    help = "Starts background tasks"

    def handle(self, *args, **kwargs):
        # Проверка, запущена ли уже задача
        if not Task.objects.filter(task_name='crypto_signals.tasks.collect_and_send_signals').exists():
            collect_and_send_signals(repeat=60)
            self.stdout.write(self.style.SUCCESS("Background task started successfully."))
        else:
            self.stdout.write(self.style.WARNING("Background task is already running."))
