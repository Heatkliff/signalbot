from django.core.management.base import BaseCommand
import logging
from crypto_signals.tools.analytic_upgraded import BingXChart
from crypto_signals.tools.autotrade import BingXTradingBot
from crypto_signals.models import TelegramConfig
import time

class Command(BaseCommand):
    help = 'Поиск новых сигналов и отправка их в группу'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Запуск задачи collect_and_create_deals..."))
        time.sleep(5)
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.config = TelegramConfig.objects.first()

        signals = []

        chart = BingXChart()
        symbols = chart.fetch_symbols()

        chart.set_interval(interval='1h')

        for symbol in symbols:
            try:
                dict_analysis = chart.generate_analytics(symbol=symbol, hours_ago=48)
            except BaseException as e:
                print(e)
                continue
            if dict_analysis['trade_signal'] != None:
                signals.append(dict_analysis)

        chart.set_interval(interval='15m')

        messages = []
        for signal in signals:
            message = "✅✅✅✅✅СДЕЛКА СИСТЕМЫ✅✅✅✅✅\n"
            message += (f"Пара: {signal['trade_signal']['монета']} \n"
                        f"Направление: {signal['trade_signal']['направление']} \n"
                        f"Вероятность: {signal['trade_signal']['вероятность отработки']} \n")

            dict_analysis = chart.generate_analytics(symbol=signal['trade_signal']['монета'], hours_ago=48)

            if dict_analysis['trade_signal'] is not None:
                if dict_analysis['trade_signal']['направление'] == signal['trade_signal']['направление']:
                    message += "✅✅✅СИГНАЛ СОВПАДАЕТ С 15m tf✅✅✅ \n"
                    self.create_deal(
                        symbol=signal['trade_signal']['монета'],
                        position=signal['trade_signal']['направление'],
                        entry_price=float(signal['trade_signal']['точка входа']),
                        take_profit=float(signal['trade_signal']['тейк поинт']),
                        stop_loss=float(signal['trade_signal']['стоп-лосс'])
                    )
                else:
                    continue
            else:
                self.create_deal(
                    symbol=signal['trade_signal']['монета'],
                    position=signal['trade_signal']['направление'],
                    entry_price=float(signal['trade_signal']['точка входа']),
                    take_profit=float(signal['trade_signal']['тейк поинт']),
                    stop_loss=float(signal['trade_signal']['стоп-лосс'])
                )
                message += "⚠️⚠️⚠️СИГНАЛ НЕ СУЩЕСТВУЕТ НА 15m tf⚠️⚠️⚠️ \n"

            message += (f"точка входа: {float(signal['trade_signal']['точка входа'])} \n"
                        f"тейк поинт: {float(signal['trade_signal']['тейк поинт'])} \n"
                        f"стоп-лосс: {float(signal['trade_signal']['стоп-лосс'])} \n")
            message += f"Коментарий от системы: \n {signal['trade_signal']['comment']} \n"
            message += "✅✅✅✅✅СДЕЛКА СИСТЕМЫ✅✅✅✅✅"
            messages.append(message)

        if len(messages) > 0:
            for message in messages:
                print(message)
        else:
            print("Новых сделок в данный момент нет")
        logger.info("Задача collect_and_create_deals выполнена")

    def create_deal(self, symbol, position, entry_price, take_profit, stop_loss):
        api_key = self.config.api_key
        secret_key = self.config.secret_key

        bot = BingXTradingBot(api_key, secret_key)

        try:
            response = bot.place_order(
                symbol=symbol,
                side="BUY",
                position_side=position,
                order_type="LIMIT",
                quantity=1,
                entry_price=entry_price,  # Оставляем None для рыночного ордера
                take_profit=take_profit,
                stop_loss=stop_loss,
                leverage=25,
            )
            print("Order placed successfully:", response)
        except Exception as e:
            print("Error placing order:", e)
