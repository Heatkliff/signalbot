from django.db import models


class TelegramConfig(models.Model):
    api_id = models.IntegerField()
    api_hash = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    admin_chat_id = models.IntegerField()
    token = models.CharField(max_length=255)
    chat_id = models.IntegerField()


class TelegramChannel(models.Model):
    config = models.ForeignKey(TelegramConfig, related_name='channels', on_delete=models.CASCADE)
    channel_name = models.CharField(max_length=255)


class SentMessage(models.Model):
    trader_name = models.CharField(max_length=255, default=" ")
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message sent at {self.timestamp}"


class DataCollectionLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    signals_count = models.IntegerField()  # Количество собранных сигналов
    info_count = models.IntegerField()  # Количество собранной информации

    def __str__(self):
        return f"Log at {self.timestamp}: {self.signals_count} signals, {self.info_count} info messages"


class Signal(models.Model):
    trader_name = models.CharField(max_length=255, default="")
    currency = models.CharField(max_length=50, blank=True, null=True)  # Валюта, по которой дается сигнал
    direction = models.CharField(max_length=50, blank=True,
                                 null=True)  # Направление сделки (текстовое поле)  # Направление сделки (покупка/продажа)
    entry = models.DecimalField(max_digits=15, decimal_places=8, blank=True, null=True)  # Уровень входа
    targets = models.JSONField(blank=True, null=True)  # Цели, можно использовать JSON для хранения списка значений
    stop_loss = models.DecimalField(max_digits=15, decimal_places=8, blank=True, null=True)  # Стоп-лосс
    timestamp = models.DateTimeField(auto_now_add=True)  # Время, когда сигнал был создан
    ema = models.IntegerField(blank=True, null=True)
    st = models.IntegerField(blank=True, null=True)
    macd = models.IntegerField(blank=True, null=True)
    rsi = models.IntegerField(blank=True, null=True)
    stoch = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.currency} ({self.direction}) at {self.entry} ({self.timestamp})"


# Модель для аналитики рынка
class MarketAnalysis(models.Model):
    time = models.DateTimeField(auto_now_add=True)  # Время создания записи
    crypto_data = models.JSONField()  # Список криптовалют с аналитикой

    def __str__(self):
        return f"Market Analysis at {self.time}"
