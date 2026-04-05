import httpx
from datetime import datetime


def fetch_binance_klines(symbol: str, interval: str, start_date: str, end_date: str) -> list:
    """Fetch klines from multiple crypto exchanges."""
    start_ms = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    end_ms = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

    all_klines = []
    current_start = start_ms

    while current_start < end_ms:
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": current_start,
            "endTime": end_ms,
            "limit": 1000
        }

        # Try Binance Data Vision first
        klines = try_binance_data_vision(params)
        if klines is None or len(klines) == 0:
            # Try Binance main API
            klines = try_binance_main(params)
        if klines is None or len(klines) == 0:
            # Try Kraken as fallback
            klines = try_kraken(symbol, interval, current_start, end_ms)

        if klines is None or len(klines) == 0:
            raise Exception("No market data available for this symbol. Please try a different symbol (e.g., BTCUSDT, ETHUSDT, BNBUSDT) or shorter time period.")

        all_klines.extend(klines)
        current_start = klines[-1][0] + 1

        if len(klines) < 1000:
            break

    return all_klines


def try_binance_data_vision(params: dict) -> list:
    """Try Binance Data Vision API - works from most regions."""
    url = "https://data-api.binance.vision/api/v3/klines"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
            elif response.status_code == 451:
                return None  # Region blocked, try next source
    except Exception:
        pass
    return None


def try_binance_main(params: dict) -> list:
    """Try Binance Main API."""
    url = "https://api.binance.com/api/v3/klines"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
            elif response.status_code == 451:
                return None
    except Exception:
        pass
    return None


def try_kraken(symbol: str, interval: str, start_ms: int, end_ms: int) -> list:
    """Fetch from Kraken API as fallback."""
    base = symbol.replace("USDT", "").replace("BTC", "XBT")
    pair = f"{base}USD"

    interval_map = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "4h": 240, "1d": 1440
    }
    kraken_interval = interval_map.get(interval, 15)

    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={kraken_interval}&since={int(start_ms/1000)}"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("error") == [] and data.get("result"):
                    result = data["result"]
                    pair_data = list(result.values())[0]
                    klines = []
                    for candle in pair_data:
                        klines.append([
                            candle[0] * 1000,
                            candle[1],
                            candle[3],
                            candle[2],
                            candle[4],
                            candle[6]
                        ])
                    return klines
    except Exception:
        pass
    return None


def parse_klines(klines: list) -> dict:
    """Parse klines into pandas-friendly format."""
    data = {
        "open_time": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": [],
    }

    for k in klines:
        try:
            data["open_time"].append(datetime.fromtimestamp(k[0] / 1000))
            data["open"].append(float(k[1]))
            data["high"].append(float(k[2]))
            data["low"].append(float(k[3]))
            data["close"].append(float(k[4]))
            data["volume"].append(float(k[5]))
        except (IndexError, ValueError):
            continue

    return data
