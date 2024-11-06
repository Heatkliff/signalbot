from django.core.management.base import BaseCommand
from crypto_signals.tools.analytics import BingXChart
from crypto_signals.models import MarketAnalysis
import time

# Management команда для заполнения данных
class Command(BaseCommand):
    help = 'Collects market analysis data and stores it in the database'

    def handle(self, *args, **kwargs):
        chart = BingXChart()
        symbols = chart.fetch_symbols()
        chart.set_interval(interval='15m')
        # print(f"Доступные торговые пары: {', '.join(symbols)}")
        # Задаем интервал для графиков
        crypto_list = []

        for symbol in symbols:
            # Получаем данные аналитики
            dict_analysis = chart.generate_analytics(symbol=symbol, hours_ago=48)
            data_analysis = {
                "name": symbol,
                "ema": dict_analysis["logic"]['ema'],
                "st": dict_analysis["logic"]['st'],
                "macd": dict_analysis["logic"]['MACD'],
                "rsi": dict_analysis["logic"]['RSI'],
                "stoch": dict_analysis["logic"]['stoch']
            }
            crypto_list.append(data_analysis)
            print(data_analysis)

        # Создание объекта модели MarketAnalysis
        analysis = MarketAnalysis.objects.create(
            crypto_data=crypto_list
        )
        analysis.save()

        self.stdout.write(self.style.SUCCESS('Successfully added market analysis data'))
