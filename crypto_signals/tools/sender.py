from datetime import datetime, timezone, timedelta
from telegram import Bot
from crypto_signals.models import SentMessage
import os
from crypto_signals.tools.signal_writer import remake_signal
import asyncio
from concurrent.futures import ThreadPoolExecutor


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
                loop = asyncio.get_running_loop()
                with ThreadPoolExecutor() as executor:
                    # Вызов синхронной функции в отдельном потоке
                    remaked_signal = await loop.run_in_executor(executor, remake_signal, message[0], message[1])

                # remaked_signal = remake_signal(message[0], message[1])
                if remaked_signal:
                    new_text = (f"Трейдер :{message[0]}\n"
                                f"Монета :{remaked_signal.get('currency')}\n"
                                f"Направление :{remaked_signal.get('direction')}\n")
                    if remaked_signal.get(
                            "entry") is not None: new_text += f"Точка входа: {remaked_signal.get('entry')}\n"
                    if remaked_signal.get(
                            "targets") is not None:
                        targets = " ".join(remaked_signal.get('targets'))
                        new_text += f"Цели: {targets} \n"
                    if remaked_signal.get(
                            "stop_loss") is not None: new_text += f"Stop loss: {remaked_signal.get('stop_loss')}\n"
                    new_text += (f"Сообщение трейдера: \n {message[1]}\n"
                                 f"Открыть сделку https://swap.bingx.com/uk-ua/{remaked_signal.get("currency")}\n")
                    await self.bot.send_message(chat_id=self.chat_id, text=new_text, parse_mode='HTML')
                    await SentMessage.objects.acreate(message_text=message[1], trader_name={message[0]})
                else:
                    await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='HTML')
                    await SentMessage.objects.acreate(message_text=message[1], trader_name={message[0]})
