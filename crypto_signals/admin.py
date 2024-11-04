from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import TelegramConfig, TelegramChannel, SentMessage, Signal
from .models import DataCollectionLog


@admin.register(DataCollectionLog)
class DataCollectionLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'signals_count', 'info_count')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(TelegramConfig)
class TelegramConfigAdmin(admin.ModelAdmin):
    list_display = ('api_id', 'phone_number', 'chat_id', 'admin_chat_id')


@admin.register(TelegramChannel)
class TelegramChannelAdmin(admin.ModelAdmin):
    list_display = ('config', 'channel_name')


@admin.register(SentMessage)
class SentMessageAdmin(admin.ModelAdmin):
    list_display = ('trader_name', 'message_text', 'timestamp')

@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ('currency', 'direction', 'entry', 'timestamp')  # Отображение полей в админке
    search_fields = ('currency', 'direction')  # Возможность поиска по валюте и направлению
    list_filter = ('currency', 'direction', 'timestamp')  # Фильтры для удобства работы

