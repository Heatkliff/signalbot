import pandas as pd
import numpy as np


class Oscillators:
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

    def calculate_pivot_points(self, df):
        df['Pivot'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        df['R1'] = 2 * df['Pivot'] - df['low'].shift(1)
        df['S1'] = 2 * df['Pivot'] - df['high'].shift(1)
        df['R2'] = df['Pivot'] + (df['high'].shift(1) - df['low'].shift(1))
        df['S2'] = df['Pivot'] - (df['high'].shift(1) - df['low'].shift(1))
        return df

    def compute_cci(self, df_base, n=20):
        df = df_base.copy()

        # Вычисление типичной цены (TP)
        df['TP'] = (df['high'] + df['low'] + df['close']) / 3

        # Вычисление скользящей средней TP
        df['SMA_TP'] = df['TP'].rolling(window=n).mean()

        # Вычисление среднего отклонения (Mean Deviation)
        def mad(x):
            return np.mean(np.abs(x - x.mean()))

        df['MAD'] = df['TP'].rolling(window=n).apply(mad, raw=False)

        # Вычисление CCI
        df['CCI'] = (df['TP'] - df['SMA_TP']) / (0.015 * df['MAD'])

        # Возврат серии CCI
        return df

    def analyze_indicators(self, df):
        analysis = []
        self.last_analytics = {}

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

        # Анализ CCI
        cci_value = df['CCI'].iloc[-1]
        if cci_value > 100:
            self.last_analytics["cci"] = 1
            analysis.append(f"CCI показывает сильный восходящий моментум ({int(cci_value)}). Возможен рост цены.")
        elif cci_value < -100:
            self.last_analytics["cci"] = -1
            analysis.append(
                f"CCI показывает сильный нисходящий моментум ({int(cci_value)}). Возможна дальнейшая просадка цены.")
        else:
            self.last_analytics["cci"] = 0
            analysis.append(f"CCI около нуля ({int(cci_value)}). Возможна боковая тенденция.")

        return analysis

    def generate_analytics(self, df_base):
        try:
            self.last_analytics = {}

            df = df_base.copy()

            df = self.calculate_rsi(df)
            df = self.calculate_stochastic(df)
            df = self.compute_cci(df)
            df = self.calculate_atr(df)
            df = self.calculate_pivot_points(df)

            self.df = df

            # Провести анализ индикаторов
            analysis_results = self.analyze_indicators(df)

            return {
                "text": analysis_results,
                "logic": self.last_analytics,
            }
        except ValueError as e:
            print(e)
