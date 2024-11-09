import asyncio
import time

from django.core.management.base import BaseCommand
import logging
from crypto_signals.tools.analytic_upgraded import BingXChart
from crypto_signals.tools.sender import SignalBot
from crypto_signals.models import TelegramConfig


class Command(BaseCommand):
    help = 'Поиск новых сигналов и отправка их в группу'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Запуск задачи collect_and_send_signals..."))
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        async def async_collect_and_send():
            signals = []

            chart = BingXChart()
            symbols = chart.fetch_symbols()

            chart.set_interval(interval='15m')

            for symbol in symbols:
                try:
                    dict_analysis = chart.generate_analytics(symbol=symbol, hours_ago=24)
                except BaseException as e:
                    print(e)
                    continue
                if dict_analysis['trade_signal'] != None:
                    signals.append(dict_analysis)

            chart.set_interval(interval='1h')

            messages = []
            for signal in signals:
                message = "✅✅✅✅✅СИГНАЛ ОТ СИСТЕМЫ✅✅✅✅✅\n"
                message += (f"Пара: {signal['trade_signal']['монета']} \n"
                            f"Направление: {signal['trade_signal']['направление']} \n"
                            f"Вероятность: {signal['trade_signal']['вероятность отработки']} \n")

                dict_analysis = chart.generate_analytics(symbol=signal['trade_signal']['монета'], hours_ago=48)

                if dict_analysis['trade_signal'] is not None:
                    if dict_analysis['trade_signal']['направление'] == signal['trade_signal']['направление']:
                        message += "✅✅✅СИГНАЛ СОВПАДАЕТ С ЧАСОВЫМ✅✅✅ \n"
                    else:
                        message += "❌❌❌СИГНАЛ НЕ СОВПАДАЕТ С ЧАСОВЫМ❌❌❌ \n"
                else:
                    message += "⚠️⚠️⚠️СИГНАЛ НЕ СУЩЕСТВУЕТ НА ЧАСОВОМ⚠️⚠️⚠️ \n"

                message += (f"точка входа: {float(signal['trade_signal']['точка входа'])} \n"
                            f"тейк поинт: {float(signal['trade_signal']['тейк поинт'])} \n"
                            f"стоп-лосс: {float(signal['trade_signal']['стоп-лосс'])} \n")
                message += "✅✅✅✅✅СИГНАЛ ОТ СИСТЕМЫ✅✅✅✅✅"
                messages.append(message)

            config = await TelegramConfig.objects.afirst()
            bot = SignalBot(config=config)
            if len(messages) > 0:
                for message in messages:
                    await bot.send_message(message)
                    time.sleep(2)
            else:
                await bot.send_message("Новых сигналов в данный момент нет")

        loop = asyncio.new_event_loop()
        loop.run_until_complete(async_collect_and_send())
        logger.info("Задача collect_and_send_signals выполнена")
