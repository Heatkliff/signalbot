import re
import json
from crypto_signals.models import Signal


def parse_crypto_signal(message, trading_pairs):
    # Определение шаблонов для поиска отдельных элементов
    patterns = {
        "direction": re.compile(r"(?P<direction>LONG|SHORT|лонг|шорт)", re.IGNORECASE),
        "entry": re.compile(r"(?:вход|ТВХ)[:\s]*(?P<entry>[\d.,]+)", re.IGNORECASE),
        "targets": re.compile(r"(?:тейк[-\s]?профит|цели|тейк)[:\s]*(?P<targets>[\d.,\s|\n-]+)", re.IGNORECASE),
        "stop_loss": re.compile(r"(?:стоп|stop[-\s]?[Ll]oss)[:\s]*(?P<stop_loss>[\d.,]+)", re.IGNORECASE)
    }

    # print(f"Processing message: {message[:50]}...")  # Добавлен отладочный вывод
    signal = {
        "currency": None,
        "direction": None,
        "entry": None,
        "targets": [],
        "stop_loss": None
    }

    # Проверка на наличие одной из торговых пар в сообщении, независимо от регистра
    for pair in trading_pairs:
        if pair.split('-')[0].lower() in message.lower():  # Проверка по названию монеты
            signal["currency"] = pair
            break

    # Если найдена валюта, продолжаем искать направление
    if signal["currency"]:
        match = patterns["direction"].search(message)
        if match:
            signal["direction"] = match.group("direction")

    # Проход по каждому шаблону для поиска остальных элементов
    for key, pattern in patterns.items():
        if key == "direction":
            continue
        for attempt in range(5):
            match = pattern.search(message)
            if match:
                if key == "targets":
                    signal[key] = [t.strip() for t in re.split(r'[|\n\s-]+', match.group("targets")) if t]
                else:
                    signal[key] = match.group(key)
                break

    # Проверка, если валюта и направление найдены, возвращаем сигнал
    if signal["currency"] and signal["direction"]:
        return signal
    else:
        print(f"No complete match found for message")  # Отладочный вывод при отсутствии совпадения
        return None


def remake_signal(trader, message):
    trading_pairs = [
        "BTC-USDT", "ETH-USDT", "LINK-USDT", "BCH-USDT", "EOS-USDT", "ADA-USDT", "XRP-USDT", "LTC-USDT", "DOT-USDT",
        "AVAX-USDT", "THETA-USDT", "ALGO-USDT", "AXS-USDT", "DYDX-USDT", "OMG-USDT", "CELR-USDT", "SHIB-USDT",
        "ICP-USDT", "SAND-USDT", "KSM-USDT", "VET-USDT", "SUSHI-USDT", "SOL-USDT", "NEAR-USDT", "ATOM-USDT", "BSV-USDT",
        "UNI-USDT", "FIL-USDT", "AAVE-USDT", "DOGE-USDT", "ENJ-USDT", "MANA-USDT", "CHZ-USDT", "TRX-USDT", "SKL-USDT",
        "ZRX-USDT", "SNX-USDT", "FTM-USDT", "CRV-USDT", "LRC-USDT", "YFI-USDT", "MKR-USDT", "1INCH-USDT", "COMP-USDT",
        "REN-USDT", "GRT-USDT", "MASK-USDT", "ENS-USDT", "BAT-USDT", "STORJ-USDT", "IMX-USDT", "XLM-USDT", "WAVES-USDT",
        "ONT-USDT", "ONE-USDT", "EGLD-USDT", "HBAR-USDT", "CELO-USDT", "KAVA-USDT", "BNB-USDT", "GALA-USDT", "YGG-USDT",
        "CHR-USDT", "APE-USDT", "KNC-USDT", "ZIL-USDT", "FLOW-USDT", "GMT-USDT", "RUNE-USDT", "RVN-USDT", "NEO-USDT",
        "IOST-USDT", "ETC-USDT", "ROSE-USDT", "MINA-USDT", "CFX-USDT", "API3-USDT", "AGLD-USDT", "SLP-USDT",
        "GLMR-USDT", "LINA-USDT", "JASMY-USDT", "BAKE-USDT", "MTL-USDT", "PEOPLE-USDT", "ANKR-USDT", "WOO-USDT",
        "HOT-USDT", "LUNC-USDT", "LUNA-USDT", "OP-USDT", "FLM-USDT", "KDA-USDT", "ICX-USDT", "LDO-USDT", "PERP-USDT",
        "STG-USDT", "INJ-USDT", "APT-USDT", "ETHW-USDT", "QNT-USDT", "ARPA-USDT", "SFP-USDT", "TONCOIN-USDT",
        "MAGIC-USDT", "HOOK-USDT", "GTC-USDT", "FXS-USDT", "USTC-USDT", "GMX-USDT", "HIGH-USDT", "BNX-USDT",
        "CORE-USDT", "COTI-USDT", "METIS-USDT", "ASTR-USDT", "DUSK-USDT", "GFT-USDT", "BLUR-USDT", "PHB-USDT",
        "STX-USDT", "ACH-USDT", "TRB-USDT", "FLOKI-USDT", "LIT-USDT", "ILV-USDT", "RLC-USDT", "LPT-USDT", "ATA-USDT",
        "CKB-USDT", "BLZ-USDT", "AMB-USDT", "SUN-USDT", "STMX-USDT", "BSW-USDT", "DAR-USDT", "IOTA-USDT", "SSV-USDT",
        "TLM-USDT", "REEF-USDT", "TWT-USDT", "SXP-USDT", "TRU-USDT", "LQTY-USDT", "ID-USDT", "ARB-USDT", "JOE-USDT",
        "EDU-USDT", "SUI-USDT", "TURBO-USDT", "ORDI-USDT", "UMA-USDT", "KEY-USDT", "COMBO-USDT", "NMR-USDT", "MAV-USDT",
        "WLD-USDT", "PENDLE-USDT", "OXT-USDT", "BNT-USDT", "CYBER-USDT", "SEI-USDT", "1000PEPE-USDT", "HIFI-USDT",
        "ARK-USDT", "KAS-USDT", "BIGTIME-USDT", "ORBS-USDT", "BOND-USDT", "WAXP-USDT", "RIF-USDT", "POLYX-USDT",
        "POWR-USDT", "GAS-USDT", "TIA-USDT", "CAKE-USDT", "MEME-USDT", "TOKEN-USDT", "BADGER-USDT", "10000SATS-USDT",
        "NTRN-USDT", "BEAM-USDT", "RATS-USDT", "PYTH-USDT", "1000BONK-USDT", "SUPER-USDT", "ONG-USDT", "JTO-USDT",
        "CTC-USDT", "AUCTION-USDT", "ACE-USDT", "MOVR-USDT", "NFP-USDT", "XAI-USDT", "WIF-USDT", "MANTA-USDT",
        "ONDO-USDT", "LSK-USDT", "ALT-USDT", "TAO-USDT", "JUP-USDT", "ZETA-USDT", "RON-USDT", "DYM-USDT", "OM-USDT",
        "PIXEL-USDT", "MAVIA-USDT", "STRK-USDT", "GLM-USDT", "PORTAL-USDT", "MYRO-USDT", "10000000AIDOGE-USDT",
        "AEVO-USDT", "VANRY-USDT", "BOME-USDT", "SLERF-USDT", "ETHFI-USDT", "DEGEN-USDT", "ENA-USDT", "W-USDT",
        "TNSR-USDT", "SAGA-USDT", "FOXY-USDT", "OMNINETWORK-USDT", "MERL-USDT", "MEW-USDT", "REZ-USDT", "BB-USDT",
        "NOT-USDT", "DOG-USDT", "IO-USDT", "1000000BABYDOGE-USDT", "GME-USDT", "BRETT-USDT", "ATH-USDT", "ZK-USDT",
        "LISTA-USDT", "ZRO-USDT", "BLAST-USDT", "MOCA-USDT", "UXLINK-USDT", "PRCL-USDT", "BANANA-USDT", "A8-USDT",
        "CLOUD-USDT", "RENDER-USDT", "MAX-USDT", "PONKE-USDT", "RARE-USDT", "G-USDT", "SYN-USDT", "SYS-USDT",
        "VOXEL-USDT", "CATI-USDT", "POPCAT-USDT", "VIDT-USDT", "NULS-USDT", "DOGS-USDT", "SUNDOG-USDT", "MBOX-USDT",
        "CHESS-USDT", "ORDER-USDT", "SWELL-USDT", "FLUX-USDT", "POL-USDT", "QUICK-USDT", "NEIROETH-USDT", "AERGO-USDT",
        "NEIROCTO-USDT", "RPL-USDT", "FIDA-USDT", "FIO-USDT", "GHST-USDT", "LOKA-USDT", "HMSTR-USDT", "EIGEN-USDT",
        "COS-USDT", "DIA-USDT", "10000WHY-USDT", "PUFFER-USDT", "CARV-USDT", "DBR-USDT", "1000CAT-USDT", "SCR-USDT",
        "GOAT-USDT", "SAFE-USDT", "SANTOS-USDT", "GRASS-USDT", "MOODENG-USDT", "TROY-USDT", "KAIA-USDT"
    ]
    rsignal = parse_crypto_signal(message, trading_pairs)

    if rsignal:
        signal = Signal.objects.create(
            trader_name=trader,
            currency=rsignal.get("currency"),
            direction=rsignal.get("direction"),
            entry=rsignal.get("entry"),
            targets=rsignal.get("targets"),
            stop_loss=rsignal.get("stop_loss")
        )

        # Сохранение объекта в базе данных
        signal.save()
        return rsignal
    else:
        return None
