"""
Crypto Backtester - Web Version
FastAPI backend with embedded HTML interface
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd
from datetime import datetime, timedelta

from utils import fetch_binance_klines, parse_klines
from indicators import add_indicators
from strategy import run_backtest

app = FastAPI(title="Crypto Backtester", version="2.0")


class BacktestRequest(BaseModel):
    symbol: str
    interval: str
    start_date: str
    end_date: str
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    rsi_min: int = 50
    rsi_max: int = 65
    stop_loss: float = 0.5
    take_profit: float = 1.0


HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Backtester</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            padding: 30px 0;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #00d4aa, #00b894);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #8b949e;
            font-size: 1rem;
        }

        .card {
            background: #161b22;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }

        .card-title {
            color: #8b949e;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-title::before {
            content: '';
            width: 3px;
            height: 16px;
            background: #00d4aa;
            border-radius: 2px;
        }

        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        label {
            color: #8b949e;
            font-size: 0.85rem;
        }

        input, select {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px 16px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.2s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #00d4aa;
            box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1);
        }

        input::placeholder {
            color: #484f58;
        }

        .chip-group {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }

        .chip {
            padding: 8px 16px;
            background: #1f2937;
            border: 1px solid #30363d;
            border-radius: 20px;
            color: #fff;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.9rem;
        }

        .chip:hover {
            border-color: #00d4aa;
        }

        .chip.active {
            background: #00d4aa;
            border-color: #00d4aa;
            color: #0d1117;
        }

        .btn {
            background: linear-gradient(135deg, #00d4aa, #00b894);
            color: #0d1117;
            border: none;
            padding: 16px 32px;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 212, 170, 0.3);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-icon {
            width: 20px;
            height: 20px;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #30363d;
            border-top-color: #00d4aa;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .results {
            display: none;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: #0d1117;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .stat-label {
            color: #8b949e;
            font-size: 0.8rem;
            margin-bottom: 8px;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
        }

        .stat-value.green { color: #00d4aa; }
        .stat-value.red { color: #ff6b6b; }

        .trades-table {
            width: 100%;
            border-collapse: collapse;
        }

        .trades-table th {
            text-align: left;
            padding: 12px 16px;
            color: #8b949e;
            font-size: 0.75rem;
            text-transform: uppercase;
            border-bottom: 1px solid #30363d;
        }

        .trades-table td {
            padding: 16px;
            border-bottom: 1px solid #21262d;
        }

        .trades-table tr:hover {
            background: #1c2128;
        }

        .trade-profit {
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 6px;
            display: inline-block;
        }

        .trade-profit.positive {
            background: rgba(0, 212, 170, 0.15);
            color: #00d4aa;
        }

        .trade-profit.negative {
            background: rgba(255, 107, 107, 0.15);
            color: #ff6b6b;
        }

        .error-msg {
            background: rgba(255, 107, 107, 0.15);
            border: 1px solid #ff6b6b;
            border-radius: 12px;
            padding: 20px;
            color: #ff6b6b;
            text-align: center;
            margin-bottom: 20px;
            display: none;
        }

        .section-title {
            color: #fff;
            font-size: 1.2rem;
            margin: 24px 0 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .section-title::after {
            content: '';
            flex: 1;
            height: 1px;
            background: #30363d;
        }

        footer {
            text-align: center;
            padding: 30px;
            color: #8b949e;
            font-size: 0.85rem;
        }

        @media (max-width: 768px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }

            .form-row {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 1.8rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Crypto Backtester</h1>
            <p class="subtitle">Test your trading strategies with real Binance data</p>
        </header>

        <div class="card">
            <div class="card-title">Market</div>
            <div class="form-row">
                <div class="form-group">
                    <label>Symbol</label>
                    <input type="text" id="symbol" value="BTCUSDT" placeholder="e.g. BTCUSDT, ETHUSDT">
                </div>
                <div class="form-group">
                    <label>Timeframe</label>
                    <div class="chip-group">
                        <button class="chip" data-interval="1m">1m</button>
                        <button class="chip" data-interval="5m">5m</button>
                        <button class="chip active" data-interval="15m">15m</button>
                        <button class="chip" data-interval="30m">30m</button>
                        <button class="chip" data-interval="1h">1h</button>
                        <button class="chip" data-interval="4h">4h</button>
                        <button class="chip" data-interval="1d">1d</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Date Range</div>
            <div class="form-row">
                <div class="form-group">
                    <label>Start Date</label>
                    <input type="date" id="startDate">
                </div>
                <div class="form-group">
                    <label>End Date</label>
                    <input type="date" id="endDate">
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Strategy Settings</div>
            <div class="form-row">
                <div class="form-group">
                    <label>Fast EMA</label>
                    <input type="number" id="emaFast" value="20">
                </div>
                <div class="form-group">
                    <label>Slow EMA</label>
                    <input type="number" id="emaSlow" value="50">
                </div>
                <div class="form-group">
                    <label>RSI Period</label>
                    <input type="number" id="rsiPeriod" value="14">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>RSI Min</label>
                    <input type="number" id="rsiMin" value="50">
                </div>
                <div class="form-group">
                    <label>RSI Max</label>
                    <input type="number" id="rsiMax" value="65">
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Stop Loss (%)</label>
                    <input type="number" id="stopLoss" value="0.5" step="0.1">
                </div>
                <div class="form-group">
                    <label>Take Profit (%)</label>
                    <input type="number" id="takeProfit" value="1.0" step="0.1">
                </div>
            </div>
        </div>

        <button class="btn" id="runBtn" onclick="runBacktest()">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
            </svg>
            Run Backtest
        </button>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Analyzing market data...</p>
        </div>

        <div class="error-msg" id="errorMsg"></div>

        <div class="results" id="results">
            <h3 class="section-title">Summary</h3>
            <div class="summary-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Trades</div>
                    <div class="stat-value" id="totalTrades">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value green" id="winRate">0%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Profit</div>
                    <div class="stat-value green" id="totalProfit">0%</div>
                </div>
            </div>

            <h3 class="section-title">Trade History</h3>
            <div class="card">
                <table class="trades-table">
                    <thead>
                        <tr>
                            <th>Entry Time</th>
                            <th>Exit Time</th>
                            <th>Entry Price</th>
                            <th>Exit Price</th>
                            <th>Profit</th>
                        </tr>
                    </thead>
                    <tbody id="tradesBody"></tbody>
                </table>
            </div>
        </div>

        <footer>
            <p>Crypto Backtester v2.0 | Real-time Market Data</p>
        </footer>
    </div>

    <script>
        let selectedInterval = '15m';

        // Set default dates
        const today = new Date();
        const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
        document.getElementById('startDate').value = weekAgo.toISOString().split('T')[0];

        // Interval chips
        document.querySelectorAll('.chip[data-interval]').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                selectedInterval = chip.dataset.interval;
            });
        });

        async function runBacktest() {
            const btn = document.getElementById('runBtn');
            const loading = document.getElementById('loading');
            const errorMsg = document.getElementById('errorMsg');
            const results = document.getElementById('results');

            // Reset UI
            errorMsg.style.display = 'none';
            results.style.display = 'none';
            btn.disabled = true;
            loading.style.display = 'block';

            const request = {
                symbol: document.getElementById('symbol').value.toUpperCase().trim(),
                interval: selectedInterval,
                start_date: document.getElementById('startDate').value,
                end_date: document.getElementById('endDate').value,
                ema_fast: parseInt(document.getElementById('emaFast').value),
                ema_slow: parseInt(document.getElementById('emaSlow').value),
                rsi_period: parseInt(document.getElementById('rsiPeriod').value),
                rsi_min: parseInt(document.getElementById('rsiMin').value),
                rsi_max: parseInt(document.getElementById('rsiMax').value),
                stop_loss: parseFloat(document.getElementById('stopLoss').value),
                take_profit: parseFloat(document.getElementById('takeProfit').value)
            };

            // Validation
            if (!request.symbol) {
                showError('Please enter a symbol');
                return;
            }
            if (!request.start_date || !request.end_date) {
                showError('Please select date range');
                return;
            }
            if (request.ema_fast >= request.ema_slow) {
                showError('Fast EMA must be less than Slow EMA');
                return;
            }
            if (request.rsi_min >= request.rsi_max) {
                showError('RSI Min must be less than RSI Max');
                return;
            }

            try {
                const response = await fetch('/backtest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(request)
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Server error');
                }

                if (data.trades.length === 0) {
                    showError('No trades found for this period. Try a longer date range.');
                    return;
                }

                displayResults(data);
            } catch (error) {
                showError(error.message || 'Failed to connect to server');
            } finally {
                btn.disabled = false;
                loading.style.display = 'none';
            }
        }

        function showError(message) {
            const errorMsg = document.getElementById('errorMsg');
            const loading = document.getElementById('loading');
            const btn = document.getElementById('runBtn');
            errorMsg.textContent = message;
            errorMsg.style.display = 'block';
            loading.style.display = 'none';
            btn.disabled = false;
        }

        function displayResults(data) {
            const results = document.getElementById('results');
            results.style.display = 'block';

            document.getElementById('totalTrades').textContent = data.summary.total_trades;

            const winRate = data.summary.win_rate.toFixed(2) + '%';
            const winRateEl = document.getElementById('winRate');
            winRateEl.textContent = winRate;
            winRateEl.className = 'stat-value ' + (data.summary.win_rate >= 50 ? 'green' : 'red');

            const profit = data.summary.total_profit_percent.toFixed(2) + '%';
            const profitEl = document.getElementById('totalProfit');
            profitEl.textContent = profit;
            profitEl.className = 'stat-value ' + (data.summary.total_profit_percent >= 0 ? 'green' : 'red');

            const tbody = document.getElementById('tradesBody');
            tbody.innerHTML = data.trades.map(trade => {
                const profitClass = trade.profit_percent >= 0 ? 'positive' : 'negative';
                const profitSign = trade.profit_percent >= 0 ? '+' : '';
                return `
                    <tr>
                        <td>${trade.entry_time}</td>
                        <td>${trade.exit_time}</td>
                        <td>${trade.entry_price.toFixed(2)}</td>
                        <td>${trade.exit_price.toFixed(2)}</td>
                        <td><span class="trade-profit ${profitClass}">${profitSign}${trade.profit_percent.toFixed(2)}%</span></td>
                    </tr>
                `;
            }).join('');

            results.scrollIntoView({ behavior: 'smooth' });
        }
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_CONTENT


@app.post("/backtest")
async def backtest(req: BacktestRequest):
    try:
        if req.ema_fast >= req.ema_slow:
            raise HTTPException(status_code=400, detail="ema_fast must be less than ema_slow")
        if req.rsi_min >= req.rsi_max:
            raise HTTPException(status_code=400, detail="rsi_min must be less than rsi_max")

        klines = fetch_binance_klines(
            symbol=req.symbol,
            interval=req.interval,
            start_date=req.start_date,
            end_date=req.end_date
        )

        if not klines:
            raise HTTPException(status_code=404, detail="No data found for given parameters")

        data = parse_klines(klines)
        df = pd.DataFrame(data)
        df = add_indicators(df, req.ema_fast, req.ema_slow, req.rsi_period)
        df = df.dropna()

        trades, summary = run_backtest(
            df=df,
            ema_fast=req.ema_fast,
            ema_slow=req.ema_slow,
            rsi_min=req.rsi_min,
            rsi_max=req.rsi_max,
            stop_loss=req.stop_loss,
            take_profit=req.take_profit
        )

        trades_list = [
            {
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "profit_percent": t.profit_percent
            }
            for t in trades
        ]

        return {"summary": summary, "trades": trades_list}

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Make error messages user-friendly
        if "Failed to connect" in error_msg or "Connection" in error_msg:
            raise HTTPException(status_code=503, detail="Cannot connect to market data servers. Please try again later.")
        elif "No market data" in error_msg or "No data available" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "Binance" in error_msg or "451" in error_msg:
            raise HTTPException(status_code=503, detail="Market data temporarily unavailable. Please try a different time period or symbol.")
        else:
            raise HTTPException(status_code=500, detail="An error occurred. Please try again.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
