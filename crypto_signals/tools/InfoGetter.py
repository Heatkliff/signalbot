import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt


class InfoGetter:
    def __init__(self):
        self.start_time = 0
        self.symbols_url = 'https://open-api.bingx.com/openApi/swap/v2/quote/contracts'
        self.klines_url = 'https://open-api.bingx.com/openApi/swap/v3/quote/klines'
        self.interval = None
        self.limit = 1440
        self.last_analytics = {}
        self.df = None

    def fetch_bing_symbols(self):
        response = requests.get(self.symbols_url)
        data = response.json()
        if data['code'] == 0:
            return [item['symbol'] for item in data['data'] if item['symbol'].endswith('USDT')]
        else:
            raise ValueError(f"Ошибка при получении списка торговых пар: {data['msg']}")

    def clear(self):
        self.df = None
        self.last_analytics = None

    def split_stages(self, stages, max_value=1436):
        # Проверяем, нужно ли разбивать
        if stages <= max_value:
            return [stages]  # Если меньше или равно max_value, возвращаем как есть

        # Разбиваем на части
        parts = []
        while stages > max_value:
            parts.append(max_value)
            stages -= max_value
        if stages > 0:
            parts.append(stages)

        return parts

    def fetch_bing_data(self, symbol, stages=25):
        # Установка начального времени
        if self.interval == "15m":
            step = timedelta(minutes=15)
        elif self.interval == "1h":
            step = timedelta(hours=1)
        elif self.interval == "4h":
            step = timedelta(hours=4)
        else:
            raise ValueError("Interval may be 1h or 15m")

        # Вычисляем временной шаг и проверяем лимит
        end_time = datetime.now()
        start_time = end_time - (step * stages)
        result_data = []

        while start_time < end_time:
            # Ограничиваем запросы блоками до 1440 записей
            next_end_time = start_time + (step * self.limit)
            if next_end_time > end_time:
                next_end_time = end_time

            # Подготовка параметров запроса
            params = {
                'symbol': symbol,
                'interval': self.interval,
                'limit': self.limit,
                'startTime': int(start_time.timestamp() * 1000),
                'endTime': int(next_end_time.timestamp() * 1000)
            }

            # Отправка запроса
            response = requests.get(self.klines_url, params=params)
            data = response.json()

            # Обработка ответа
            if data['code'] == 0:
                result_data.extend(data['data'])
            else:
                raise ValueError(f"Ошибка при получении данных для {symbol}: {data['msg']}")

            # Переход к следующему интервалу
            start_time = next_end_time

        return result_data

    def plot_graph_data(self, symbol, graph_data):
        # Преобразуем данные в DataFrame
        df = pd.DataFrame(list(graph_data.items()), columns=['timestamp', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['close'] = df['close'].astype(float)
        df['close'] = df['close'].fillna(method='ffill')

        # Построение графика
        plt.figure(figsize=(10, 6))
        plt.plot(df['timestamp'], df['close'], label=f'{symbol} Close Price')
        plt.title(f'{symbol} Price Chart')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.show()

    def create_dataframe(self, klines):
        df = pd.DataFrame(klines, columns=['open', 'close', 'high', 'low', 'volume', 'time'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index('time', inplace=True)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df = df.iloc[1:]
        df = df.iloc[::-1]
        return df

    def prepare_data(self, symbol, interval, hours_ago=25):
        self.interval = interval
        data = self.fetch_bing_data(symbol, hours_ago)
        df_data = self.create_dataframe(data)
        return df_data
