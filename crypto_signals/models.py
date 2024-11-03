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
