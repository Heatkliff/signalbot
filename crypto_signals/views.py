from django.shortcuts import render
from .models import SentMessage, DataCollectionLog
from datetime import datetime
from django.http import JsonResponse


def home_view(request):
    # Получаем статус задачи
    data_log = DataCollectionLog.objects.last()
    task_status = 'Не запланирована'
    last_run = None

    # Получаем последние 50 сигналов
    recent_signals = SentMessage.objects.order_by('-timestamp')[:50]

    # Передаем данные в шаблон
    context = {
        'task_status': task_status,
        'last_run': data_log.timestamp if data_log else None,
        'recent_signals': recent_signals,
    }
    return render(request, 'home.html', context)


def sent_messages_list(request):
    # Извлечение всех текстов сообщений из модели SentMessage
    messages = SentMessage.objects.values_list('message_text', flat=True)

    # Формирование списка сообщений
    messages_list = list(messages)

    # Возвращение данных в формате JSON
    return JsonResponse({'messages': messages_list}, json_dumps_params={'ensure_ascii': False})
