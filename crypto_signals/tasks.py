import logging
from background_task import background
from crypto_signals.tools.collector import TelegramSignalScraper
from crypto_signals.tools.sender import SignalBot
from .models import DataCollectionLog, TelegramConfig

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@background(schedule=60)
def collect_and_send_signals():
    # Создаем объект для сбора сигналов
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
