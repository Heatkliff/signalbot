from datetime import datetime, timezone, timedelta
from telegram import Bot
from .models import SentMessage
import os


class SignalBot:
    def __init__(self, config):
        # Используем переданную конфигурацию
        self.token = config.token
        self.chat_id = config.chat_id
        self.bot = Bot(token=self.token)

    async def send_messages(self, messages):
        for message in messages:
            local_time = message[2].astimezone(timezone(timedelta(hours=2)))
            text = f"Трейдер {message[0]} в {local_time.strftime('%H:%M:%S')} Сигнал:\n{message[1]}"

            if not await SentMessage.objects.filter(message_text=message[1]).aexists():
                await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='HTML')
                await SentMessage.objects.acreate(message_text=message[1], trader_name={message[0]})
