import time
import requests
import hmac
from hashlib import sha256


class BingXTradingBot:
    def __init__(self, api_key, secret_key, api_url="https://open-api.bingx.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.api_url = api_url

    def _get_sign(self, payload):
        """Генерация подписи HMAC SHA256"""
        return hmac.new(
            self.secret_key.encode("utf-8"), payload.encode("utf-8"), sha256
        ).hexdigest()

    def _send_request(self, method, path, params, payload=None):
        """Отправка HTTP-запроса к API"""
        params_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = self._get_sign(params_str)
        url = f"{self.api_url}{path}?{params_str}&signature={signature}"
        headers = {"X-BX-APIKEY": self.api_key}

        response = requests.request(method, url, headers=headers, data=payload)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code}, {response.text}")
        return response.json()

    def place_order(
            self,
            symbol,
            side,
            position_side,
            order_type,
            quantity,
            entry_price=None,
            take_profit=None,
            stop_loss=None,
            leverage=1,
    ):
        """
        Создание сделки
        :param symbol: Торговая пара, например "BTC-USDT"
        :param side: BUY или SELL
        :param position_side: LONG или SHORT
        :param order_type: MARKET или LIMIT
        :param quantity: Сумма в USDT
        :param entry_price: Цена входа (для лимитного ордера)
        :param take_profit: Цена тейк-профита
        :param stop_loss: Цена стоп-лосса
        :param leverage: Множитель
        :return: Ответ API
        """
        path = "/openApi/swap/v2/trade/order"

        params = {
            "symbol": symbol,
            "side": side,
            "positionSide": position_side,
            "type": order_type,
            "leverage": leverage,
            "timestamp": int(time.time() * 1000),
        }

        if position_side == "LONG":
            params['side'] = "BUY"
        elif position_side == "SHORT":
            params['side'] = "SELL"

        # Для лимитного ордера добавляем entry_price
        if order_type == "LIMIT" and entry_price:
            params["price"] = entry_price
        quantity_real = (quantity * leverage) / entry_price
        params['quantity'] = quantity_real

        # Добавляем тейк-профит и стоп-лосс в формате JSON строки
        if take_profit:
            params["takeProfit"] = (
                f'{{"type": "TAKE_PROFIT_MARKET", "stopPrice": {take_profit}, "price": {take_profit}, "workingType": "MARK_PRICE"}}'
            )
        if stop_loss:
            params["stopLoss"] = (
                f'{{"type": "STOP_MARKET", "stopPrice": {stop_loss}, "price": {stop_loss}, "workingType": "MARK_PRICE"}}'
            )

        return self._send_request("POST", path, params)
