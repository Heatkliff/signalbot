import asyncio
import time

from django.core.management.base import BaseCommand
import logging
from crypto_signals.tools.analytic_upgraded import BingXChart
from crypto_signals.tools.collector import TelegramSignalScraper
from crypto_signals.tools.sender import SignalBot
from crypto_signals.models import DataCollectionLog, TelegramConfig


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

            # Задаем интервал для графиков
            chart.set_interval(interval='15m')

            # Получаем данные аналитики

            for symbol in symbols:
                dict_analysis = chart.generate_analytics(symbol=symbol, hours_ago=24)
                if dict_analysis['trade_signal'] != None:
                    signals.append(dict_analysis)

            messages = []
            for signal in signals:
                message = "✅✅✅✅✅СИГНАЛ ОТ СИСТЕМЫ✅✅✅✅✅\n"
                message += (f"Пара: {signal['trade_signal']['монета']} \n"
                            f"Направление: {signal['trade_signal']['направление']} \n"
                            f"Вероятность: {signal['trade_signal']['вероятность отработки']} \n"
                            f"точка входа: {float(signal['trade_signal']['точка входа'])} \n"
                            f"тейк поинт: {float(signal['trade_signal']['тейк поинт'])} \n"
                            f"стоп-лосс: {float(signal['trade_signal']['стоп-лосс'])} \n")
                message += "✅✅✅✅✅СИГНАЛ ОТ СИСТЕМЫ✅✅✅✅✅"
                messages.append(message)

            if len(messages) > 0:
                config = await TelegramConfig.objects.afirst()
                bot = SignalBot(config=config)
                for message in messages:
                    await bot.send_message(message)
                    time.sleep(2)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(async_collect_and_send())
        logger.info("Задача collect_and_send_signals выполнена")
