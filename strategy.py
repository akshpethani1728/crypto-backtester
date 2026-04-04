import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class Trade:
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    profit_percent: float


def is_bullish_candle(df: pd.DataFrame, idx: int) -> bool:
    """Check if candle is bullish (close > open)."""
    return df["close"].iloc[idx] > df["open"].iloc[idx]


def check_buy_signal(
    df: pd.DataFrame,
    idx: int,
    ema_fast: int,
    ema_slow: int,
    rsi_min: int,
    rsi_max: int
) -> bool:
    """Check if buy signal is triggered."""
    if idx < 1:
        return False

    ema_fast_val = df["ema_fast"].iloc[idx]
    ema_slow_val = df["ema_slow"].iloc[idx]
    price = df["close"].iloc[idx]
    rsi = df["rsi"].iloc[idx]

    if ema_fast_val <= ema_slow_val:
        return False

    if abs(price - ema_fast_val) / ema_fast_val > 0.001:
        return False

    if not (rsi_min <= rsi <= rsi_max):
        return False

    if not is_bullish_candle(df, idx):
        return False

    return True


def check_sell_signal(df: pd.DataFrame, idx: int, ema_fast: int, ema_slow: int) -> bool:
    """Check if sell signal is triggered (opposite trend)."""
    if idx < 1:
        return False

    ema_fast_val = df["ema_fast"].iloc[idx]
    ema_slow_val = df["ema_slow"].iloc[idx]

    if ema_fast_val >= ema_slow_val:
        return False

    return True


def run_backtest(
    df: pd.DataFrame,
    ema_fast: int,
    ema_slow: int,
    rsi_min: int,
    rsi_max: int,
    stop_loss: float,
    take_profit: float
) -> tuple:
    """
    Run backtesting strategy on dataframe.
    Returns (trades, summary)
    """
    trades = []
    in_position = False
    entry_price = 0.0
    entry_time = None

    for idx in range(1, len(df)):
        price = df["close"].iloc[idx]
        current_time = df["open_time"].iloc[idx].strftime("%Y-%m-%d %H:%M")

        if not in_position:
            if check_buy_signal(df, idx, ema_fast, ema_slow, rsi_min, rsi_max):
                in_position = True
                entry_price = price
                entry_time = current_time

        else:
            change_percent = ((price - entry_price) / entry_price) * 100

            sell_reason = None

            if change_percent <= -stop_loss:
                sell_reason = "stop_loss"
            elif change_percent >= take_profit:
                sell_reason = "take_profit"
            elif check_sell_signal(df, idx, ema_fast, ema_slow):
                sell_reason = "signal"

            if sell_reason:
                exit_price = price
                exit_time = current_time
                profit_percent = ((exit_price - entry_price) / entry_price) * 100

                trades.append(Trade(
                    entry_time=entry_time,
                    exit_time=exit_time,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    profit_percent=round(profit_percent, 4)
                ))

                in_position = False
                entry_price = 0.0
                entry_time = None

    total_trades = len(trades)
    if total_trades == 0:
        return trades, {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_profit_percent": 0.0
        }

    winning_trades = sum(1 for t in trades if t.profit_percent > 0)
    win_rate = (winning_trades / total_trades) * 100
    total_profit = sum(t.profit_percent for t in trades)

    summary = {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_profit_percent": round(total_profit, 4)
    }

    return trades, summary
