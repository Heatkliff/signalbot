from django.core.management.base import BaseCommand
from crypto_signals.tools.analytic_upgraded import BingXChart
from crypto_signals.models import HistorySignal
import time
from datetime import datetime, timedelta


# Management команда для заполнения данных
class Command(BaseCommand):
    help = 'Collects market analysis data and stores it in the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Waiting 3 seconds'))
        time.sleep(3)
        self.stdout.write(self.style.SUCCESS('Successfully started 1h signals data'))
        chart = BingXChart()
        symbols = chart.fetch_symbols()
        chart.set_interval(interval='1h')

        for symbol in symbols:
            # Получаем данные аналитики
            dict_analysis = chart.generate_analytics(symbol=symbol, hours_ago=48)
            if dict_analysis['trade_signal'] is not None:
                try:
                    price_data = float(chart.get_current_price(symbol))
                    tpls = self.remake_marks(dict_analysis['trade_signal']['направление'], price_data, chart)

                    current_signal = HistorySignal.objects.create(
                        symbol=symbol,
                        type_signal="1h",
                        position=dict_analysis['trade_signal']['направление'],
                        entry=price_data,
                        take=tpls['tp'],
                        stop=tpls['sl'],
                        timestamp=self.round_past_time_to_nearest_interval(0, 60)
                    )
                    current_signal.save()
                except Exception as e:
                    print(f"ERROR {e}")

        self.stdout.write(self.style.SUCCESS('Successfully added 1h signals data'))

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

    def round_past_time_to_nearest_interval(self, minutes_ago, interval_minutes):
        """
        Округляет заданное время (в прошлом) до ближайшего значения, кратного интервалу в минутах.

        :param minutes_ago: Сколько минут назад от текущего времени нужно взять для расчёта.
        :param interval_minutes: Интервал в минутах, до которого нужно округлить время.
        :return: Округлённое время в виде объекта datetime.
        TODO: Имеем проблем с тем что нас гонит не на час назад а на ближайшую точку
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
