import httpx
from datetime import datetime


def fetch_binance_klines(symbol: str, interval: str, start_date: str, end_date: str) -> list:
    """Fetch klines from Binance Data API (works globally)."""
    # Use Binance Data API - works from any region
    url = "https://data-api.binance.vision/api/v3/klines"

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

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                klines = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 451:
                raise Exception("Binance is not available in your region. Please try a different time period.")
            raise Exception(f"Binance API error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to connect to Binance: {str(e)}")

        if not klines:
            break

        all_klines.extend(klines)
        current_start = klines[-1][0] + 1

        if len(klines) < 1000:
            break

    return all_klines


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
