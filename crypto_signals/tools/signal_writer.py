import re
import json
from crypto_signals.models import Signal


def parse_crypto_signal(message, trading_pairs):
    # Определение шаблонов для поиска отдельных элементов
    patterns = {
        "direction": re.compile(r"(?P<direction>LONG|SHORT|лонг|шорт)", re.IGNORECASE),
        "entry": re.compile(r"(?:вход|ТВХ)[:\s]*(?P<entry>[\d.,]+)", re.IGNORECASE),
        "targets": re.compile(r"(?:тейк[-\s]?профит|цели|тейк)[:\s]*(?P<targets>[\d.,\s|\n-]+)", re.IGNORECASE),
        "stop_loss": re.compile(r"(?:стоп|stop[-\s]?[Ll]oss)[:\s]*(?P<stop_loss>[\d.,]+)", re.IGNORECASE)
    }

    print(f"Processing message: {message[:50]}...")  # Добавлен отладочный вывод
    signal = {
        "currency": None,
        "direction": None,
        "entry": None,
        "targets": [],
        "stop_loss": None
    }

    # Проверка на наличие одной из торговых пар в сообщении, независимо от регистра
    for pair in trading_pairs:
        if pair.split('-')[0].lower() in message.lower():  # Проверка по названию монеты
            signal["currency"] = pair
            break

    # Если найдена валюта, продолжаем искать направление
    if signal["currency"]:
        match = patterns["direction"].search(message)
        if match:
            signal["direction"] = match.group("direction")

    # Проход по каждому шаблону для поиска остальных элементов
    for key, pattern in patterns.items():
        if key == "direction":
            continue
        for attempt in range(5):
            match = pattern.search(message)
            if match:
                if key == "targets":
                    signal[key] = [t.strip() for t in re.split(r'[|\n\s-]+', match.group("targets")) if t]
                else:
                    signal[key] = match.group(key)
                break

    # Проверка, если валюта и направление найдены, возвращаем сигнал
    if signal["currency"] and signal["direction"]:
        return signal
    else:
        print(f"No complete match found for message")  # Отладочный вывод при отсутствии совпадения
        return None
