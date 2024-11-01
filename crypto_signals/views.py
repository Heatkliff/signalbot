from django.shortcuts import render
from background_task.models import Task
from .models import SentMessage
from datetime import datetime

def home_view(request):
    # Получаем статус задачи
    task = Task.objects.filter(task_name='crypto_signals.tasks.collect_and_send_signals').first()
    task_status = 'Не запланирована'
    last_run = None
    if task:
        task_status = 'В процессе' if task.lock else 'Запланирована'
        last_run = task.run_at

    # Получаем последние 50 сигналов
    recent_signals = SentMessage.objects.order_by('-timestamp')[:50]

    # Передаем данные в шаблон
    context = {
        'task_status': task_status,
        'last_run': last_run,
        'recent_signals': recent_signals,
    }
    return render(request, 'home.html', context)
