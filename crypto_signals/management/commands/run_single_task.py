from django.core.management.base import BaseCommand
import logging
from crypto_signals.tools.collector import TelegramSignalScraper
from crypto_signals.tools.sender import SignalBot
from crypto_signals.models import DataCollectionLog, TelegramConfig


class Command(BaseCommand):
    help = 'Однократный запуск задачи collect_and_send_signals'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Запуск задачи collect_and_send_signals..."))
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        scraper = TelegramSignalScraper()

        async def async_collect_and_send():
            await scraper.connect()
            await scraper.scrape_channels()

            signals = scraper.signals
            info = scraper.info

            await DataCollectionLog.objects.acreate(
                signals_count=len(signals),
                info_count=len(info)
            )

            if signals:
                config = await TelegramConfig.objects.afirst()
                bot = SignalBot(config=config)
                await bot.send_messages(signals)
                logger.info("Задача collect_and_send_signals выполнена")

        # Запуск асинхронной функции в явно созданном цикле событий
        scraper.loop.run_until_complete(async_collect_and_send())
        self.stdout.write(self.style.SUCCESS("Задача успешно выполнена."))
