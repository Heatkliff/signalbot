from django.shortcuts import render
from .models import SentMessage, DataCollectionLog, MarketAnalysis
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
    return render(request, 'info/home.html', context)


def sent_messages_list(request):
    # Извлечение всех текстов сообщений из модели SentMessage
    messages = SentMessage.objects.values_list('message_text', flat=True)

    # Формирование списка сообщений
    messages_list = list(messages)

    # Возвращение данных в формате JSON
    return JsonResponse({'messages': messages_list}, json_dumps_params={'ensure_ascii': False})


def market_analysis_view(request):
    # Получение самой последней записи анализа
    analysis = MarketAnalysis.objects.latest('time')
    crypto_data = analysis.crypto_data

    # Преобразование значений
    for crypto in crypto_data:
        crypto['ema'] = 'long' if crypto['ema'] == 1 else 'short' if crypto['ema'] == -1 else 'боковое'
        crypto['st'] = 'long' if crypto['st'] == 1 else 'short' if crypto['st'] == -1 else 'боковое'
        crypto['macd'] = 'long' if crypto['macd'] == 1 else 'short' if crypto['macd'] == -1 else 'боковое'
        crypto['rsi'] = 'long' if crypto['rsi'] == 1 else 'short' if crypto['rsi'] == -1 else 'боковое'
        crypto['stoch'] = 'long' if crypto['stoch'] == 1 else 'short' if crypto['stoch'] == -1 else 'боковое'

        # Определение ожидаемого результата
        long_count = sum([1 for k in ['ema', 'st', 'macd', 'rsi', 'stoch'] if crypto[k] == 'long'])
        short_count = sum([1 for k in ['ema', 'st', 'macd', 'rsi', 'stoch'] if crypto[k] == 'short'])

        if long_count >= 4:
            crypto['expected_result'] = 'Высокая вероятность лонг'
            crypto['result_class'] = 'text-success'
            crypto['sort_priority'] = 1
        elif long_count == 3:
            crypto['expected_result'] = 'Низкая вероятность лонг'
            crypto['result_class'] = 'text-success text-info'
            crypto['sort_priority'] = 2
        elif short_count >= 4:
            crypto['expected_result'] = 'Высокая вероятность шорта'
            crypto['result_class'] = 'text-danger'
            crypto['sort_priority'] = 1
        elif short_count == 3:
            crypto['expected_result'] = 'Низкая вероятность шорта'
            crypto['result_class'] = 'text-warning'
            crypto['sort_priority'] = 2
        else:
            crypto['expected_result'] = 'Вероятно боковое движение'
            crypto['result_class'] = 'text-warning text-dark'
            crypto['sort_priority'] = 3

    # Сортировка списка по параметру 'sort_priority'
    crypto_data.sort(key=lambda x: x['sort_priority'])

    return render(request, 'info/market_analysis.html', {'crypto_data': crypto_data})
