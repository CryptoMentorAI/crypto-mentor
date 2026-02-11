# CryptoMentor — Educational Paper Trading Bot

## Project Overview
Educational crypto paper trading bot yang auto-trade dan **explain setiap keputusan** dalam Bahasa Melayu.
Tujuan utama: belajar trading secara praktikal, bukan profit semata.

## Tech Stack
- **Backend**: Python 3.14 + FastAPI
- **Frontend**: Next.js 14 + TypeScript + TailwindCSS
- **Charts**: TradingView Lightweight Charts
- **Exchange**: Bybit Testnet (paper trading) / Mock data mode
- **Database**: SQLite (via SQLAlchemy async)
- **Technical Analysis**: pandas-ta

## How to Run

### Backend
```bash
cd Desktop/crypto-mentor
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

### Frontend
```bash
cd Desktop/crypto-mentor/frontend
npm install
npm run dev
```

### URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Architecture
- `backend/core/` — Market data engine, paper trader, bot loop, config
- `backend/strategies/` — 4 strategies (technical, price_action, trend, scalping) + orchestrator
- `backend/explainer/` — Trade explanation engine + trading concepts glossary
- `backend/api/` — REST routes + WebSocket handlers
- `backend/database/` — SQLAlchemy models + DB init
- `frontend/src/app/` — Pages (dashboard, trade detail, learn, settings)
- `frontend/src/components/` — Chart, TradeLog, ExplanationCard, PortfolioStats

## Key Features
1. 4 Trading Strategies with confluence scoring
2. Explanation Engine — every trade comes with full BM explanation
3. Post-Trade Analysis — lessons learned after each trade
4. Learning Center — trading concepts glossary in BM
5. Mock mode — runs without Bybit API keys
6. Real-time WebSocket updates

## Environment
- Set `MOCK_MODE=true` in `backend/.env` for simulated data (default)
- Set `MOCK_MODE=false` + add Bybit testnet API keys for real testnet data
