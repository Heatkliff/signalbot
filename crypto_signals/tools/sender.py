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

                if remaked_signal:
                    direction = str(remaked_signal.get('direction')).upper()
                    new_text = (f"Трейдер :{message[0]}\n"
                                f"Монета :{remaked_signal.get('currency')}\n"
                                f"Направление :{remaked_signal.get('direction')}\n")
                    if remaked_signal.get(
                            "entry") is not None: new_text += f"Точка входа: {remaked_signal.get('entry')}\n"
                    if remaked_signal.get(
                            "targets") is not None and len(remaked_signal["targets"]) > 0:
                        targets = " ".join(remaked_signal.get('targets'))
                        new_text += f"Цели: {targets} \n"
                    if remaked_signal.get(
                            "stop_loss") is not None: new_text += f"Stop loss: {remaked_signal.get('stop_loss')}\n"
                    new_text += "==========Аналитика==========\n"
                    recomendation_indicator = remaked_signal['ema'] + remaked_signal['st'] + remaked_signal['macd'] + \
                                              remaked_signal['rsi'] + remaked_signal['stoch']
                    if direction == "SHORT": recomendation_indicator = recomendation_indicator * -1
                    new_text += (
                        f"\n EMA: {remaked_signal['ema']}, ST: {remaked_signal['st']}, MACD: {remaked_signal['macd']},"
                        f" RSI: {remaked_signal['rsi']}, STOCH: {remaked_signal['stoch']}, INDICATOR: {recomendation_indicator}\n")
                    new_text += f"\n http://crypto-alien-bot.pp.ua/status_market/{message[0].upper()}\n"
                    new_text += "\n=========Рекомендации========\n"

                    if recomendation_indicator < -2:
                        new_text += "❌❌❌Крайне низкая вероятность отработки❌❌❌ \n"
                    elif -2 <= recomendation_indicator < 2:
                        new_text += "⚠️⚠️⚠️Низкая вероятность отработки⚠️⚠️⚠️ \n"
                    elif 2 <= recomendation_indicator < 4:
                        new_text += "✅✅✅Высокая вероятность отработки✅✅✅ \n"
                    elif recomendation_indicator >= 4:
                        new_text += "💰💰💰Крайне высокая вероятность отработки💰💰💰 \n"

                    features_link = "https://swap.bingx.com/uk-ua/" + str(remaked_signal.get("currency"))
                    new_text += (f"Сообщение трейдера: \n {message[1]}\n"
                                 f"Открыть сделку {features_link} \n")
                    await self.bot.send_message(chat_id=self.chat_id, text=new_text, parse_mode='HTML')
                    await SentMessage.objects.acreate(message_text=message[1], trader_name={message[0]})
                else:
                    await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='HTML')
                    await SentMessage.objects.acreate(message_text=message[1], trader_name={message[0]})
