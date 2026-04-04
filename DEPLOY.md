# Crypto Backtester Web - Deployment Guide

## Quick Deploy to Render.com (Free)

### Step 1: Push to GitHub

1. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name it: `crypto-backtester`
   - Make it Public
   - Click "Create repository"

2. Push the code (run these commands in `trading-backtest-web` folder):
```bash
cd C:\Users\Petha\trading-backtest-web
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/crypto-backtester.git
git push -u origin main
```

### Step 2: Deploy on Render.com

1. Go to https://render.com and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   - **Name**: crypto-backtester
   - **Region**: Singapore (nearest to you)
   - **Branch**: main
   - **Root Directory**: (leave empty)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click "Create Web Service"
6. Wait for deployment (2-5 minutes)
7. Your URL will be: `https://crypto-backtester.onrender.com`

### Step 3: Update Android App

1. Edit: `trading-backtest-android/app/src/main/java/com/backtester/api/RetrofitClient.kt`
2. Change `BASE_URL` to your Render URL:
```kotlin
const val BASE_URL = "https://crypto-backtester.onrender.com/"
```

---

## Alternative: Deploy to Railway

1. Go to https://railway.app
2. Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repo
5. Railway will auto-detect FastAPI and deploy

---

## Local Testing

Run locally:
```bash
cd C:\Users\Petha\trading-backtest-web
pip install -r requirements.txt
python main.py
```

Then open: http://localhost:8000

---

## Features

- Works on any device with browser
- Same API for web and mobile
- Fetches real Binance data
- EMA + RSI strategy backtesting
- Dark themed UI
