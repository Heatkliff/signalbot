from concurrent.futures import ThreadPoolExecutor
from analytic.oscillators import Oscillators
from analytic.trend import TrendIndicator
from InfoGetter import InfoGetter
import pandas as pd
from ban_list import banned_symbol

class Analytic:
    def __init__(self):
        self.trends = TrendIndicator()
        self.oscillators = Oscillators()
        self.confidence_threshold = 0.8  # Повышенный порог уверенности
        self.weights = {
            'supertrend': 0.35,
            'ema': 0.2,
            'macd': 0.2,
            'rsi': 0.1,
            'stochastic': 0.1,
            'cci': 0.05
        }

    def clear(self):
        self.trends.clear()
        self.oscillators.clear()

    def analytic(self, symbol, interval="1h", df_train=None):
        if df_train is None:
            getter = InfoGetter()
            df = getter.prepare_data(symbol, interval, 100)
        else:
            df = df_train

        df['volume_avg'] = df['volume'].ewm(span=50).mean()  # Используем EMA вместо SMA для гибкости

        with ThreadPoolExecutor() as executor:
            future_trend = executor.submit(self.trends.generate_analytics, df)
            future_oscillator = executor.submit(self.oscillators.generate_analytics, df)

            trend_data = future_trend.result()
            osc_data = future_oscillator.result()

        df['atr_avg'] = self.oscillators.df['ATR'].rolling(window=100).mean()  # Средний ATR за 100 свечей

        osc_df = self.oscillators.df.iloc[-1].to_dict()

        osc_data['logic']['R1'] = osc_df['R1']
        osc_data['logic']['S1'] = osc_df['S1']

        osc_data['logic']['R2'] = osc_df['R2']
        osc_data['logic']['S2'] = osc_df['S2']

        last_row = df.iloc[-1].to_dict()

        return {
            'data' : last_row,
            'trend': trend_data['logic'],
            'oscillator': osc_data['logic'],
        }

    def determine_market_type(self, trend_signals, oscillator_signals):
        if trend_signals['supertrend'] == 1 and trend_signals['ema'] == 1 and trend_signals['macd'] == 1:
            return "trend"
        elif oscillator_signals['rsi'] == 0 and oscillator_signals['stoch'] == 0 and oscillator_signals['cci'] == 0:
            return "flat"
        return "uncertain"

    def generate_trade_signal(self, indicators):
        trend_signals = indicators['trend']
        oscillator_signals = indicators['oscillator']

        market_type = self.determine_market_type(trend_signals, oscillator_signals)

        weighted_trend = sum(self.weights[k] * v for k, v in trend_signals.items() if k in self.weights)
        weighted_oscillator = sum(self.weights[k] * v for k, v in oscillator_signals.items() if k in self.weights)

        if weighted_trend > 0 and weighted_oscillator > 0:
            direction = 'LONG'
        elif weighted_trend < 0 and weighted_oscillator < 0:
            direction = 'SHORT'
        else:
            return {'signal': 'HOLD', 'message': 'Сигналы не совпадают или нейтральны.'}

        entry_point = indicators['data']['close']
        atr = indicators['oscillator']['atr']
        avg_atr = indicators['data'].get('atr_avg', atr)
        pivot_r2 = indicators['oscillator'].get('R2', entry_point + 4 * atr)
        pivot_r1 = indicators['oscillator'].get('R1', entry_point + 3.5 * atr)
        pivot_s1 = indicators['oscillator'].get('S1', entry_point - 3 * atr)
        pivot_s2 = indicators['oscillator'].get('S2', entry_point - 3.5 * atr)
        avg_volume = indicators['data'].get('volume_avg', 0)
        current_volume = indicators['data'].get('volume', 0)

        # Фильтр по объему: вход только если объем выше среднего
        if current_volume < avg_volume * 0.9:  # Гибкость при малых изменениях объема
            return {'signal': 'HOLD', 'message': 'Объем слишком низкий для входа.'}

        if atr > avg_atr * 1.5:
            return {'signal': 'HOLD', 'message': 'ATR слишком высокий, избегаем входа.'}

        if direction == 'LONG':
            stop_loss = max(entry_point - (3 * atr), pivot_s2)
            take_profit = min(entry_point + (4 * atr), pivot_r2)
        else:
            stop_loss = min(entry_point + (3 * atr), pivot_r2)
            take_profit = max(entry_point - (4 * atr), pivot_s2)

        # Динамический трейлинг-стоп: перемещение ближе при достижении 2x ATR прибыли
        trailing_stop = entry_point + (2.5 * atr) if direction == 'LONG' else entry_point - (2.5 * atr)
        if take_profit - entry_point >= 2 * atr:
            trailing_stop = entry_point + (2 * atr) if direction == 'LONG' else entry_point - (2 * atr)

        # # FILTER LIED SIGNAL
        changes_for_take = ((take_profit - entry_point) / entry_point) * 100
        if direction != 'LONG':
            changes_for_take = changes_for_take * -1

        if changes_for_take < 1.5:
            return {'signal': 'HOLD', 'message': 'Объем слишком низкий для входа.'}

        return {
            'signal': direction,
            'entry_point': entry_point,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'trailing_stop': trailing_stop,
            'market_type': market_type
        }

# TODO: NEED TO ADDING TO WORKFLOW