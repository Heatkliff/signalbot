import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class BingXChart:
    def __init__(self, test=False, past_hour=1):
        self.test_mode = test
        self.past_hour = past_hour
        self.start_time = 0
        self.symbols_url = 'https://open-api.bingx.com/openApi/swap/v2/quote/contracts'
        self.klines_url = 'https://open-api.bingx.com/openApi/swap/v3/quote/klines'
        self.mprice_url = 'https://open-api.bingx.com/openApi/swap/v2/quote/premiumIndex'
        self.interval = None
        self.limit = 1000
        self.last_analytics = {}
        self.df = None

    def fetch_symbols(self):
        response = requests.get(self.symbols_url)
        data = response.json()
        if data['code'] == 0:
            return [item['symbol'] for item in data['data'] if item['symbol'].endswith('USDT')]
        else:
            raise ValueError(f"Ошибка при получении списка торговых пар: {data['msg']}")

    def get_current_price(self, symbol):
        params = {
            'symbol': symbol,
        }
        response = requests.get(self.mprice_url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']['markPrice']
        else:
            raise ValueError(f"Ошибка при получении данных для {symbol}: {data['msg']}")

    def set_interval(self, interval):
        self.interval = interval

    def clear(self):
        self.df = None
        self.last_analytics = None

    def fetch_data(self, symbol, hours_ago=25):
        if self.test_mode:
            hours_ago += self.past_hour

        if not self.interval:
            raise ValueError("Интервал должен быть задан перед получением данных.")
        start_time = int((datetime.now() - timedelta(hours=hours_ago)).timestamp() * 1000)
        self.start_time = start_time
        params = {
            'symbol': symbol,
            'interval': self.interval,
            'limit': self.limit,
            'startTime': start_time
        }
        response = requests.get(self.klines_url, params=params)
        data = response.json()
        if data['code'] == 0:
            return data['data']
        else:
            raise ValueError(f"Ошибка при получении данных для {symbol}: {data['msg']}")

    def create_dataframe(self, klines):
        df = pd.DataFrame(klines, columns=['open', 'close', 'high', 'low', 'volume', 'time'])
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df.set_index('time', inplace=True)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        df = df.iloc[1:]
        if self.test_mode:
            df = df.iloc[self.past_hour - 1:]
        df = df.iloc[::-1]
        return df

    def calculate_ema(self, df, periods=[9, 21]):
        for period in periods:
            df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df

    def calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        df['MACD'] = df['close'].ewm(span=fast_period, adjust=False).mean() - df['close'].ewm(span=slow_period,
                                                                                              adjust=False).mean()
        df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        return df

    def calculate_supertrend(self, base_df, period=7, multiplier=3):
        df = base_df.copy()
        # Расчет ATR вручную вместо использования pandas_ta
        df['TR'] = np.maximum(df['high'] - df['low'],
                              np.maximum(abs(df['high'] - df['close'].shift(1)),
                                         abs(df['low'] - df['close'].shift(1))))
        df['atr'] = df['TR'].rolling(window=period).mean()
        df.dropna(inplace=True)

        # Расчет базовых верхней и нижней полос
        hl2 = (df['high'] + df['low']) / 2
        df['basicUpperband'] = hl2 + (multiplier * df['atr'])
        df['basicLowerband'] = hl2 - (multiplier * df['atr'])

        # Инициализация списков для хранения значений верхней и нижней полос
        first_upperBand_value = df['basicUpperband'].iloc[0]
        first_lowerBand_value = df['basicLowerband'].iloc[0]
        upperBand = [first_upperBand_value]
        lowerBand = [first_lowerBand_value]

        for i in range(1, len(df)):
            if df['basicUpperband'].iloc[i] < upperBand[i - 1] or df['close'].iloc[i - 1] > upperBand[i - 1]:
                upperBand.append(df['basicUpperband'].iloc[i])
            else:
                upperBand.append(upperBand[i - 1])

            if df['basicLowerband'].iloc[i] > lowerBand[i - 1] or df['close'].iloc[i - 1] < lowerBand[i - 1]:
                lowerBand.append(df['basicLowerband'].iloc[i])
            else:
                lowerBand.append(lowerBand[i - 1])

        df['upperBand'] = upperBand
        df['lowerBand'] = lowerBand

        # Определение направления тренда и расчет Supertrend
        df['Supertrend'] = np.nan
        in_uptrend = True

        for current in range(1, len(df.index)):
            previous = current - 1

            if df['close'].iloc[current] > df['upperBand'].iloc[previous]:
                in_uptrend = True
            elif df['close'].iloc[current] < df['lowerBand'].iloc[previous]:
                in_uptrend = False

            if in_uptrend:
                df.at[df.index[current], 'Supertrend'] = df['lowerBand'].iloc[current]
            else:
                df.at[df.index[current], 'Supertrend'] = df['upperBand'].iloc[current]

        base_df['Supertrend'] = df['Supertrend']
        base_df['upperBand'] = df['upperBand']
        base_df['lowerBand'] = df['lowerBand']
        base_df['basicUpperband'] = df['basicUpperband']
        base_df['basicLowerband'] = df['basicLowerband']
        base_df['atr'] = df['atr']

        return base_df

    def calculate_rsi(self, df, periods=[7, 14]):
        for period in periods:
            delta = df['close'].diff(1)
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            rs = avg_gain / avg_loss
            df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        return df

    def calculate_stochastic(self, df, k_period=14, d_period=3):
        df['L14'] = df['low'].rolling(window=k_period).min()
        df['H14'] = df['high'].rolling(window=k_period).max()
        df['%K'] = 100 * ((df['close'] - df['L14']) / (df['H14'] - df['L14']))
        df['%D'] = df['%K'].rolling(window=d_period).mean()
        return df

    def calculate_atr(self, df, period=14):
        df['TR'] = np.maximum(df['high'] - df['low'],
                              np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
        df['ATR'] = df['TR'].rolling(window=period).mean()
        return df

    def calculate_obv(self, df):
        df['OBV'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        return df

    def calculate_adl(self, df):
        df['MFM'] = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        df['MFV'] = df['MFM'] * df['volume']
        df['ADL'] = df['MFV'].cumsum()
        return df

    def calculate_pivot_points(self, df):
        df['Pivot'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        df['R1'] = 2 * df['Pivot'] - df['low'].shift(1)
        df['S1'] = 2 * df['Pivot'] - df['high'].shift(1)
        df['R2'] = df['Pivot'] + (df['high'].shift(1) - df['low'].shift(1))
        df['S2'] = df['Pivot'] - (df['high'].shift(1) - df['low'].shift(1))
        return df

    def calculate_profit_long(self, initial_margin, entry_price, exit_price, leverage=25):
        """
        Рассчитывает прибыль для лонг позиции с заданным кредитным плечом.

        initial_margin : float : начальный капитал (маржа)
        entry_price    : float : цена входа в позицию
        exit_price     : float : цена закрытия позиции
        leverage       : int   : кредитное плечо (по умолчанию x25)
        """
        # Вычисление изменения цены
        price_change_percent = ((exit_price - entry_price) / entry_price) * 100
        # Вычисление прибыли с учетом плеча
        profit_percent = price_change_percent * leverage
        profit = (profit_percent / 100) * initial_margin
        return profit

    def calculate_profit_short(self, initial_margin, entry_price, exit_price, leverage=25):
        """
        Рассчитывает прибыль для шорт позиции с заданным кредитным плечом.

        initial_margin : float : начальный капитал (маржа)
        entry_price    : float : цена входа в позицию
        exit_price     : float : цена закрытия позиции
        leverage       : int   : кредитное плечо (по умолчанию x25)
        """
        # Вычисление изменения цены для шорт позиции (обратное изменение цены)
        price_change_percent = ((entry_price - exit_price) / entry_price) * 100
        # Вычисление прибыли с учетом плеча
        profit_percent = price_change_percent * leverage
        profit = (profit_percent / 100) * initial_margin
        return profit

    def analyze_indicators(self, df):
        analysis = []
        self.last_analytics = {}

        # Анализ пересечения EMA
        if df['EMA_9'].iloc[-1] > df['EMA_21'].iloc[-1]:
            self.last_analytics["ema"] = 1
            analysis.append("Тренд восходящий по EMA. Возможно дальнейшее повышение.")
        else:
            self.last_analytics["ema"] = -1
            analysis.append("Тренд нисходящий по EMA. Возможно дальнейшее снижение.")

        # Анализ Supertrend
        if df['close'].iloc[-1] > df['Supertrend'].iloc[-1]:
            self.last_analytics["supertrend"] = 1
            analysis.append("Supertrend поддерживает восходящее движение.")
        else:
            self.last_analytics["supertrend"] = -1
            analysis.append("Supertrend указывает на нисходящее движение.")

        # Анализ MACD
        if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1]:
            self.last_analytics["macd"] = 1
            analysis.append("MACD указывает на бычий тренд. Возможно дальнейшее повышение.")
        else:
            self.last_analytics["macd"] = -1
            analysis.append("MACD указывает на медвежий тренд. Возможно дальнейшее снижение.")

        # Анализ RSI
        if df['RSI_14'].iloc[-1] > 70:
            self.last_analytics["rsi"] = -1
            analysis.append("RSI показывает перекупленность. Возможен откат.")
        elif df['RSI_14'].iloc[-1] < 30:
            self.last_analytics["rsi"] = 1
            analysis.append("RSI показывает перепроданность. Возможен рост.")
        else:
            self.last_analytics["rsi"] = 0
            analysis.append("RSI в нейтральной зоне.")

        # Анализ стохастика
        if df['%K'].iloc[-1] > df['%D'].iloc[-1] and df['%K'].iloc[-1] < 80:
            self.last_analytics["stoch"] = 1
            analysis.append("Стохастик показывает бычий сигнал. Возможно дальнейшее повышение.")
        elif df['%K'].iloc[-1] < df['%D'].iloc[-1] and df['%K'].iloc[-1] > 20:
            self.last_analytics["stoch"] = -1
            analysis.append("Стохастик показывает медвежий сигнал. Возможно дальнейшее снижение.")
        elif df['%K'].iloc[-1] > 80:
            self.last_analytics["stoch"] = -1
            analysis.append("Стохастик в зоне перекупленности. Возможен откат.")
        elif df['%K'].iloc[-1] < 20:
            self.last_analytics["stoch"] = 1
            analysis.append("Стохастик в зоне перепроданности. Возможен рост.")

        # Анализ ATR для определения волатильности
        if df['ATR'].iloc[-1]:
            self.last_analytics["atr"] = float(df['ATR'].iloc[-1])
            analysis.append(f"Текущая волатильность (ATR): {df['ATR'].iloc[-1]:.2f}.")

        # Анализ OBV для подтверждения тренда
        if df['OBV'].diff().iloc[-1] > 0:
            self.last_analytics["obv"] = 1
            analysis.append("OBV подтверждает восходящее движение.")
        else:
            self.last_analytics["obv"] = -1
            analysis.append("OBV подтверждает нисходящее движение.")

        # Анализ линии накопления/распределения (ADL) для понимания силы тренда
        if df['ADL'].diff().iloc[-1] > 0:
            self.last_analytics["adl"] = 1
            analysis.append("Линия накопления/распределения указывает на накопление, тренд может усиливаться.")
        else:
            self.last_analytics["adl"] = -1
            analysis.append("Линия накопления/распределения указывает на распределение, возможен разворот.")

        # Анализ Pivot Points
        close_price = df['close'].iloc[-1]
        pivot, r1, s1, r2, s2 = df['Pivot'].iloc[-1], df['R1'].iloc[-1], df['S1'].iloc[-1], df['R2'].iloc[-1], \
            df['S2'].iloc[-1]
        if close_price > pivot:
            self.last_analytics["pivot"] = 1
            analysis.append("Цена выше точки Pivot, что может указывать на продолжение роста.")
        else:
            self.last_analytics["pivot"] = -1
            analysis.append("Цена ниже точки Pivot, что может указывать на продолжение снижения.")

        if close_price > r1:
            analysis.append("Цена выше первого уровня сопротивления (R1), возможно продолжение роста.")
        elif close_price < s1:
            analysis.append("Цена ниже первого уровня поддержки (S1), возможно продолжение снижения.")

        return analysis

    def calculate_target_price(self, entry_price, leverage, target_profit_percent, position):
        """
        Вычисляет цену для достижения заданной прибыли при фьючерсной торговле.

        :param entry_price: Начальная цена (вход)
        :param leverage: Кредитное плечо (например, 25)
        :param target_profit_percent: Желаемая прибыль в процентах (например, 15)
        :param position: Тип позиции ("LONG" или "SHORT")
        :return: Необходимая цена для достижения прибыли
        """
        if position == "LONG":
            # Для позиции LONG цена должна вырасти
            target_price = entry_price * (1 + (target_profit_percent / (leverage * 100)))
        elif position == "SHORT":
            # Для позиции SHORT цена должна снизиться
            target_price = entry_price * (1 - (target_profit_percent / (leverage * 100)))
        else:
            raise ValueError("Position must be 'LONG' or 'SHORT'.")

        return target_price

    def generate_trade_signal(self, symbol, df):
        # Подсчет количества индикаторов, подтверждающих лонг и шорт
        indicators = {
            'ema': self.last_analytics.get('ema', 0),
            'supertrend': self.last_analytics.get('supertrend', 0),
            'macd': self.last_analytics.get('macd', 0),
            'obv': self.last_analytics.get('obv', 0),
            'rsi': self.last_analytics.get('rsi', 0),
            'stoch': self.last_analytics.get('stoch', 0),
            'adl': self.last_analytics.get('adl', 0),
            'pivot': self.last_analytics.get('pivot', 0)
        }
        comment = ""

        total_indicators = len(indicators)

        # Подсчет индикаторов, подтверждающих лонг и шорт
        long_count = sum(1 for value in indicators.values() if value == 1)
        short_count = sum(1 for value in indicators.values() if value == -1)

        # Расчет вероятности в процентах
        long_probability = (long_count / total_indicators) * 100
        short_probability = (short_count / total_indicators) * 100

        # Условия для генерации сигнала с вероятностью >= 70%
        if long_probability >= 80:
            direction = "LONG"
            entry_point = df['close'].iloc[-1]
            take_profit = self.calculate_target_price(df['close'].iloc[-1], 25, 20, "LONG")
            stop_loss = df['low'].iloc[-1]
            probability = long_probability - 10  # Вероятность отработки сигнала с учетом поправки
            comment += f"{long_count} индикаторов из {total_indicators} указывают на {direction} "
        elif short_probability >= 80:
            direction = "SHORT"
            entry_point = df['close'].iloc[-1]
            take_profit = self.calculate_target_price(df['close'].iloc[-1], 25, 20, "SHORT")
            stop_loss = df['high'].iloc[-1]
            probability = short_probability - 10
            comment += f"{short_count} индикаторов из {total_indicators} указывают на {direction} "

        else:
            return None  # Если условия не выполнены, сигнал не создается

        # Формируем сигнал
        signal = {
            "comment": comment,
            "монета": symbol,
            "направление": direction,
            "точка входа": entry_point,
            "тейк поинт": take_profit,
            "стоп-лосс": stop_loss,
            "вероятность отработки": f"{probability}%"
        }
        return signal

    def generate_analytics(self, symbol, hours_ago=24):
        try:
            self.last_analytics = {}

            if not self.interval:
                raise ValueError(
                    "Пожалуйста, используйте метод set_interval(interval), чтобы задать интервал перед генерацией графика.")
            klines = self.fetch_data(symbol, hours_ago)
            df = self.create_dataframe(klines)

            df = self.calculate_ema(df)
            df = self.calculate_macd(df)
            df = self.calculate_rsi(df)
            df = self.calculate_stochastic(df)
            df = self.calculate_atr(df)
            df = self.calculate_obv(df)
            df = self.calculate_adl(df)
            df = self.calculate_pivot_points(df)
            df = self.calculate_supertrend(df, period=10, multiplier=3)

            self.df = df

            # Провести анализ индикаторов
            analysis_results = self.analyze_indicators(df)

            # Генерируем торговый сигнал на основе анализа
            trade_signal = self.generate_trade_signal(symbol, df)

            return {
                "text": analysis_results,
                "logic": self.last_analytics,
                "trade_signal": trade_signal  # возвращаем сигнал
            }
        except ValueError as e:
            print(e)
