from django.core.management.base import BaseCommand
from crypto_signals.tools.analytic_upgraded import BingXChart
from crypto_signals.models import HistorySignal, TelegramConfig
from datetime import datetime, timedelta
from crypto_signals.tools.autotrade import BingXTradingBot


# Management команда для заполнения данных
class Command(BaseCommand):
    help = 'Collects market analysis data and stores it in the database'

    def handle(self, *args, **kwargs):
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
                            current_signal = HistorySignal.objects.create(
                                symbol=signal.symbol,
                                type_signal="15m",
                                position=dict_analysis['trade_signal']['направление'],
                                entry=float(dict_analysis['trade_signal']['точка входа']),
                                take=float(dict_analysis['trade_signal']['тейк поинт']),
                                stop=float(dict_analysis['trade_signal']['стоп-лосс']),
                                timestamp=self.round_past_time_to_nearest_interval(0, 60)
                            )
                            current_signal.save()

                            self.create_deal(
                                symbol=dict_analysis['trade_signal']['монета'],
                                position=dict_analysis['trade_signal']['направление'],
                                entry_price=float(dict_analysis['trade_signal']['точка входа']),
                                take_profit=float(dict_analysis['trade_signal']['тейк поинт']),
                                stop_loss=float(dict_analysis['trade_signal']['стоп-лосс'])
                            )

                            fftm_signals.append(current_signal)
                        except Exception as e:
                            print(f"ERROR {e}")
            if len(fftm_signals) == 0:
                print("Without signals")

        self.stdout.write(self.style.SUCCESS('Successfully added 15m signals data'))

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
                quantity=2,
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
