import pandas as pd
import numpy as np


class TrendIndicator:
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

    def clear(self):
        self.df = None
        self.last_analytics = None

    def calculate_ema(self, df, periods=[9, 21]):
        for period in periods:
            df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df

    def calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        df['MACD'] = df['close'].ewm(span=fast_period, adjust=False).mean() - df['close'].ewm(span=slow_period,
                                                                                              adjust=False).mean()
        df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        return df

    def calculate_parabolic_sar(self, df, step=0.02, max_step=0.2):
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values

        length = len(df)
        psar = close.copy()
        psar[0] = low[0]  # Начальное значение SAR
        bull = True  # Начинаем с бычьего тренда
        af = step
        ep = high[0]

        for i in range(1, length):
            if bull:
                psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
                psar[i] = min(psar[i], low[i - 1], low[i])
                if low[i] < psar[i]:
                    bull = False
                    psar[i] = ep
                    af = step
                    ep = low[i]
            else:
                psar[i] = psar[i - 1] + af * (ep - psar[i - 1])
                psar[i] = max(psar[i], high[i - 1], high[i])
                if high[i] > psar[i]:
                    bull = True
                    psar[i] = ep
                    af = step
                    ep = high[i]
            if bull:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + step, max_step)
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + step, max_step)

        df['parabolic_sar'] = psar
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

        # Анализ Parabolic SAR
        if df['close'].iloc[-1] > df['parabolic_sar'].iloc[-1]:
            self.last_analytics["parabolic_sar"] = 1
            analysis.append("Parabolic SAR поддерживает восходящее движение.")
        else:
            self.last_analytics["parabolic_sar"] = -1
            analysis.append("Parabolic SAR указывает на нисходящее движение.")

        # Анализ Ишимоку Кинко Хё
        # Проверяем, что необходимые столбцы существуют в DataFrame
        required_columns = ['tenkan_sen', 'kijun_sen', 'senkou_span_a', 'senkou_span_b', 'chikou_span']
        if all(column in df.columns for column in required_columns):
            # Последние значения линий индикатора
            tenkan_sen = df['tenkan_sen'].iloc[-1]
            kijun_sen = df['kijun_sen'].iloc[-1]
            senkou_span_a = df['senkou_span_a'].iloc[-26]  # Сдвиг на 26 периодов назад
            senkou_span_b = df['senkou_span_b'].iloc[-26]  # Сдвиг на 26 периодов назад
            chikou_span = df['chikou_span'].iloc[-1]
            close_price = df['close'].iloc[-1]

            # Сигналы Ишимоку
            signal = 0  # 1 для бычьего сигнала, -1 для медвежьего

            # Пересечение Tenkan-sen и Kijun-sen
            if df['tenkan_sen'].iloc[-2] < df['kijun_sen'].iloc[-2] and tenkan_sen > kijun_sen:
                signal += 1
                analysis.append("Бычий крест: Tenkan-sen пересек Kijun-sen снизу вверх.")
            elif df['tenkan_sen'].iloc[-2] > df['kijun_sen'].iloc[-2] and tenkan_sen < kijun_sen:
                signal -= 1
                analysis.append("Медвежий крест: Tenkan-sen пересек Kijun-sen сверху вниз.")

            # Положение цены относительно облака (Kumo)
            if close_price > max(senkou_span_a, senkou_span_b):
                signal += 1
                analysis.append("Цена находится выше облака Ишимоку. Восходящий тренд.")
            elif close_price < min(senkou_span_a, senkou_span_b):
                signal -= 1
                analysis.append("Цена находится ниже облака Ишимоку. Нисходящий тренд.")
            else:
                analysis.append("Цена внутри облака Ишимоку. Рынок в неопределенности.")

            # Положение Chikou Span относительно цены 26 периодов назад
            if chikou_span > df['close'].shift(26).iloc[-1]:
                signal += 1
                analysis.append("Chikou Span выше цены 26 периодов назад. Подтверждение восходящего тренда.")
            elif chikou_span < df['close'].shift(26).iloc[-1]:
                signal -= 1
                analysis.append("Chikou Span ниже цены 26 периодов назад. Подтверждение нисходящего тренда.")
            else:
                analysis.append("Chikou Span совпадает с ценой 26 периодов назад. Нейтральный сигнал.")

            # Суммарный сигнал Ишимоку
            if signal > 0:
                self.last_analytics["ichimoku"] = 1
            elif signal < 0:
                self.last_analytics["ichimoku"] = -1
            else:
                self.last_analytics["ichimoku"] = 0

        else:
            analysis.append("Недостаточно данных для расчета индикатора Ишимоку Кинко Хё.")

        return analysis

    def calculate_ichimoku(self, df):
        # Определение периодов по умолчанию
        tenkan_period = 9
        kijun_period = 26
        senkou_span_b_period = 52
        displacement = 26  # Сдвиг вперед для Senkou Span A и B

        # Расчет Tenkan-sen (линия преобразования)
        df['tenkan_sen'] = (
                                   df['high'].rolling(window=tenkan_period).max() +
                                   df['low'].rolling(window=tenkan_period).min()
                           ) / 2

        # Расчет Kijun-sen (базовая линия)
        df['kijun_sen'] = (
                                  df['high'].rolling(window=kijun_period).max() +
                                  df['low'].rolling(window=kijun_period).min()
                          ) / 2

        # Расчет Senkou Span A (линия опережения A)
        df['senkou_span_a'] = (
                (df['tenkan_sen'] + df['kijun_sen']) / 2
        ).shift(displacement)

        # Расчет Senkou Span B (линия опережения B)
        df['senkou_span_b'] = (
                                      df['high'].rolling(window=senkou_span_b_period).max() +
                                      df['low'].rolling(window=senkou_span_b_period).min()
                              ) / 2
        df['senkou_span_b'] = df['senkou_span_b'].shift(displacement)

        # Расчет Chikou Span (задержанная линия)
        df['chikou_span'] = df['close'].shift(-displacement)

        # Возвращаем DataFrame с добавленными столбцами
        return df

    def generate_analytics(self, df_base):
        try:
            self.last_analytics = {}

            df = df_base.copy()

            df = self.calculate_ema(df)
            df = self.calculate_macd(df)
            df = self.calculate_parabolic_sar(df)
            df_for_ichi = df.copy()
            df = self.calculate_supertrend(df, period=10, multiplier=3)
            df_ichi = self.calculate_ichimoku(df_for_ichi)
            df['tenkan_sen'] = df_ichi['tenkan_sen']
            df['kijun_sen'] = df_ichi['kijun_sen']
            df['senkou_span_a'] = df_ichi['senkou_span_a']
            df['senkou_span_b'] = df_ichi['senkou_span_b']
            df['chikou_span'] = df_ichi['chikou_span']

            self.df = df

            # Провести анализ индикаторов
            analysis_results = self.analyze_indicators(df)

            return {
                "text": analysis_results,
                "logic": self.last_analytics,
            }
        except ValueError as e:
            print(e)
