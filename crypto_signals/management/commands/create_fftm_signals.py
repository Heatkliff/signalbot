from django.core.management.base import BaseCommand
from crypto_signals.tools.analytic_upgraded import BingXChart
from crypto_signals.models import HistorySignal, TelegramConfig
from datetime import datetime, timedelta
from crypto_signals.tools.autotrade import BingXTradingBot
from crypto_signals.tools.sender import SignalBot

import asyncio
import time


# Management команда для заполнения данных
class Command(BaseCommand):
    help = 'Collects market analysis data and stores it in the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Waiting 3 seconds'))
        time.sleep(3)
        self.stdout.write(self.style.SUCCESS('Successfully started 15m signals data'))
        self.config = TelegramConfig.objects.first()

        need_ts = self.round_past_time_to_nearest_interval(0, 60)
        signals = HistorySignal.objects.filter(timestamp__gte=need_ts, type_signal="1h")
        if signals.count() != 0:
            chart = BingXChart()
            chart.set_interval(interval='15m')
            fftm_signals = []

            for signal in signals:
                dict_analysis = chart.generate_analytics(symbol=signal.symbol, hours_ago=12)
                if dict_analysis['trade_signal'] is not None:
                    if dict_analysis['trade_signal']['направление'] == signal.position:
                        try:

                            price_data = float(chart.get_current_price(signal.symbol))
                            if price_data > float(dict_analysis['trade_signal']['тейк поинт']):
                                continue
                            tpls = self.remake_marks(dict_analysis['trade_signal']['направление'], price_data, chart)

                            self.create_deal(
                                symbol=dict_analysis['trade_signal']['монета'],
                                position=dict_analysis['trade_signal']['направление'],
                                entry_price=price_data,
                                take_profit=tpls['tp'],
                                stop_loss=tpls['sl'],
                            )

                            current_signal = HistorySignal.objects.create(
                                symbol=signal.symbol,
                                type_signal="15m",
                                position=dict_analysis['trade_signal']['направление'],
                                entry=price_data,
                                take=tpls['tp'],
                                stop=tpls['sl'],
                                timestamp=self.round_past_time_to_nearest_interval(0, 15)
                            )
                            current_signal.save()

                            fftm_signals.append(current_signal)
                        except Exception as e:
                            print(f"ERROR {e}")

            if len(fftm_signals) == 0:
                print("Without signals")
            else:
                messages = []
                for fftm_signal in fftm_signals:
                    message = (f"✅✅✅СДЕЛКА СИСТЕМЫ✅✅✅\n"
                               f"Пара: {fftm_signal.symbol} \n"
                               f"Направление: {fftm_signal.position} \n"
                               f"точка входа: {fftm_signal.entry} \n"
                               f"тейк поинт: {fftm_signal.take} \n"
                               f"стоп-лосс: {fftm_signal.stop} \n"
                               f"Аналитика: http://crypto-alien-bot.pp.ua/status_market/{fftm_signal.symbol} \n"
                               "✅✅✅✅✅СДЕЛКА СИСТЕМЫ✅✅✅✅✅")
                    messages.append(message)
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.async_send(messages))

        self.stdout.write(self.style.SUCCESS('Successfully added 15m signals data'))

    def remake_marks(self, direction, price, chart):
        data = {}
        if direction == "LONG":
            entry_point = price
            take_profit = chart.calculate_target_price(entry_point, 25, 20, "LONG")
            stop_loss = chart.calculate_target_price(entry_point, 25, 60, "SHORT")
            data = {
                'tp': take_profit,
                'sl': stop_loss,
            }
        elif direction == "SHORT":
            entry_point = price
            take_profit = chart.calculate_target_price(entry_point, 25, 20, "SHORT")
            stop_loss = chart.calculate_target_price(entry_point, 25, 60, "LONG")
            data = {
                'tp': take_profit,
                'sl': stop_loss,
            }
        return data

    async def async_send(self, messages):
        bot = SignalBot(config=self.config)
        if len(messages) > 0:
            for message in messages:
                await bot.send_message(message)
                time.sleep(1)

    def create_deal(self, symbol, position, entry_price, take_profit, stop_loss):
        api_key = self.config.api_key
        secret_key = self.config.secret_key

        bot = BingXTradingBot(api_key, secret_key)

        try:
            response = bot.place_order(
                symbol=symbol,
                side="BUY",
                position_side=position,
                order_type="MARKET",
                quantity=1,
                entry_price=entry_price,
                take_profit=take_profit,
                stop_loss=stop_loss,
                leverage=25,
            )
            print("Order placed successfully:", response)
        except Exception as e:
            print("Error placing order:", e)

    def round_past_time_to_nearest_interval(self, minutes_ago, interval_minutes):
        """
        Округляет заданное время (в прошлом) до ближайшего значения, кратного интервалу в минутах.

        :param minutes_ago: Сколько минут назад от текущего времени нужно взять для расчёта.
        :param interval_minutes: Интервал в минутах, до которого нужно округлить время.
        :return: Округлённое время в виде объекта datetime.
        """
        now = datetime.now()
        # Вычисляем время в прошлом
        past_time = now - timedelta(minutes=minutes_ago)
        # Вычисляем количество секунд в интервале
        interval_seconds = interval_minutes * 60
        # Преобразуем время в секунды с начала дня
        seconds_since_midnight = past_time.hour * 3600 + past_time.minute * 60 + past_time.second
        # Округляем секунды вниз до ближайшего интервала
        rounded_seconds = (seconds_since_midnight // interval_seconds) * interval_seconds
        # Получаем округлённое время
        rounded_time = past_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            seconds=rounded_seconds)
        return rounded_time
