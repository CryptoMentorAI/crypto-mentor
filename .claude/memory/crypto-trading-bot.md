# Crypto Trading Educator Bot

## Project Overview
Educational paper trading bot yang auto-trade dan EXPLAIN setiap keputusan. Tujuan utama: belajar trading secara praktikal.

## Requirements
- **Exchange**: Bybit Testnet (paper trading)
- **Strategies**: ALL (Technical Analysis, Price Action, Trend Following, Scalping)
- **Interface**: Web Dashboard (with charts, trade logs, explanation panel)
- **Core Feature**: Explanation engine - setiap trade ada explanation KENAPA bot buy/sell
- **User Level**: Full stack developer

## Key Features
1. Auto-trade on Bybit Testnet
2. Explanation engine - human-readable reasoning for every trade
3. Multiple strategy support (TA, Price Action, Trend, Scalping)
4. Web dashboard with TradingView charts
5. Trade history & performance tracking
6. Post-trade analysis (betul ke salah, kenapa)

## Tech Stack (Planned)
- **Backend**: Python (FastAPI) - best for trading/TA libraries
- **Frontend**: React/Next.js + TradingView Lightweight Charts
- **Exchange API**: ccxt / pybit (Bybit SDK)
- **Technical Analysis**: pandas-ta / ta-lib
- **Database**: SQLite (simple) or PostgreSQL
- **Real-time**: WebSocket for live updates

## Status
- Planning phase - architecture design in progress
