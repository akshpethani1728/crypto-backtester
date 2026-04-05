import httpx
from datetime import datetime


def fetch_binance_klines(symbol: str, interval: str, start_date: str, end_date: str) -> list:
    """Fetch klines from Binance API with multiple fallback attempts."""
    url = "https://api.binance.com/api/v3/klines"
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

        # Try multiple times with different approaches
        klines = None
        errors = []

        # Attempt 1: Standard Binance API
        for attempt in range(3):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
                with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
                    response = client.get(url, params=params)
                    if response.status_code == 200:
                        klines = response.json()
                        break
                    elif response.status_code == 451:
                        errors.append("Binance blocked in this region (451)")
                    else:
                        errors.append(f"Binance API error: {response.status_code}")
            except Exception as e:
                errors.append(f"Attempt {attempt + 1} failed: {str(e)}")

        if klines is None:
            # If Binance fails completely, try alternative approaches
            klines = try_alternative_sources(symbol, interval, current_start, end_ms, errors)
            if klines is None:
                raise Exception(f"Failed to fetch data. Errors: {'; '.join(errors[:3])}")

        if not klines:
            break

        all_klines.extend(klines)
        current_start = klines[-1][0] + 1

        if len(klines) < 1000:
            break

    return all_klines


def try_alternative_sources(symbol: str, interval: str, start_ms: int, end_ms: int, errors: list) -> list:
    """Try alternative crypto data sources if Binance fails."""

    # Clean symbol for other APIs
    clean_symbol = symbol.upper().replace("USDT", "")

    # Try Binance DEX API (sometimes has different restrictions)
    try:
        dex_url = f"https://api.binance.org/v1/klines?symbol={clean_symbol}USDT&interval={interval}&limit=1000"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(dex_url)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return data
    except:
        pass

    # Try Yahoo Finance via rapidapi or direct
    try:
        # Use cryptoCompare API (free, no auth needed for basic use)
        interval_map = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": "1D"
        }
        period = interval_map.get(interval, 15)
        limit = min(1000, int((end_ms - start_ms) / (60000 * period)))

        crypto_url = "https://min-api.cryptocompare.com/data/v2/histominute"
        params = {
            "fsym": clean_symbol,
            "tsym": "USDT",
            "limit": limit,
            "api_key": ""  # Can work without API key for limited requests
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.get(crypto_url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("Response") == "Success" and data.get("Data"):
                    klines = []
                    for candle in data["Data"]["Data"]:
                        # Convert to binance format: [open_time, open, high, low, close, volume]
                        klines.append([
                            candle["time"] * 1000,
                            str(candle["open"]),
                            str(candle["high"]),
                            str(candle["low"]),
                            str(candle["close"]),
                            str(candle["volumefrom"])
                        ])
                    return klines
    except Exception as e:
        errors.append(f"CryptoCompare failed: {str(e)}")

    # Try Binance US (different API)
    try:
        us_url = "https://api.binance.us/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.get(us_url, params=params)
            if response.status_code == 200:
                return response.json()
    except:
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
