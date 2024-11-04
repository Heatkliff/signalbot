import os
import re
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
from datetime import datetime, timedelta, timezone
from crypto_signals.models import TelegramConfig, TelegramChannel
from asgiref.sync import sync_to_async  # Добавляем этот импорт


class TelegramSignalScraper:
    def __init__(self):
        # Получаем конфигурацию из базы данных
        config = TelegramConfig.objects.first()
        if not config:
            raise ValueError("Не найдена конфигурация Telegram. Проверьте настройки в базе данных.")

        self.api_id = config.api_id
        self.api_hash = config.api_hash
        self.phone_number = config.phone_number

        # Явное создание и передача цикла событий
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = TelegramClient('session_name', self.api_id, self.api_hash, loop=self.loop)
        self.signals = []
        self.info = []

    async def connect(self):
        await self.client.start(phone=self.phone_number)

    async def scrape_channels(self):
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(minutes=60)
        channel_entities = await self.load_channel_entities()

        for channel_name, entity in channel_entities.items():
            print(f"Подключаемся к каналу: {channel_name}")
            try:
                history = await self.client(GetHistoryRequest(
                    peer=entity,
                    limit=100,
                    offset_date=None,
                    offset_id=0,
                    max_id=0,
                    min_id=0,
                    add_offset=0,
                    hash=0
                ))

                messages = history.messages
                for msg in messages:
                    if msg.date and msg.date >= one_hour_ago:
                        if msg.message:
                            signal = self.analyze_signal_message(msg.message)
                            if signal:
                                self.signals.append([channel_name, signal, msg.date])
                            else:
                                info_message = self.analyze_info_message(msg.message)
                                if info_message:
                                    self.info.append([channel_name, info_message])

            except Exception as e:
                print(f"Ошибка при получении сообщений из канала {channel_name}: {e}")

    async def load_channel_entities(self):
        dialogs = await self.client.get_dialogs()
        channel_names = await sync_to_async(list)(TelegramChannel.objects.values_list('channel_name', flat=True))
        return {dialog.name: dialog.entity for dialog in dialogs if dialog.is_channel and dialog.name in channel_names}

    def analyze_signal_message(self, message):
        message_upper = message.upper()
        if 'LONG' in message_upper or 'SHORT' in message_upper:
            return message
        return None

    def analyze_info_message(self, message):
        message_upper = message.upper()
        if 'USDT' in message_upper:
            return message
        return None

    def __del__(self):
        # Закрытие клиента и цикла событий
        self.client.disconnect()
        self.loop.close()
