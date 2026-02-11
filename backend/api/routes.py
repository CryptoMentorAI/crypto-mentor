from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from backend.database.db import get_session
from backend.database.models import (
    Trade, TradeExplanation, PostAnalysis, MarketSnapshot,
    Portfolio, StrategyConfig,
)
from backend.core.market_data import market_data
from backend.core.config import settings
from backend.explainer.concepts import get_concept, get_all_concepts, search_concepts

router = APIRouter()


# ─── Dashboard ───────────────────────────────

@router.get("/dashboard")
async def get_dashboard(session: AsyncSession = Depends(get_session)):
    """Main dashboard data — portfolio, recent trades, current price."""
    portfolio = (await session.execute(select(Portfolio).limit(1))).scalars().first()

    recent_trades = (await session.execute(
        select(Trade).order_by(desc(Trade.created_at)).limit(10)
    )).scalars().all()

    open_trades = (await session.execute(
        select(Trade).where(Trade.status == "OPEN").order_by(desc(Trade.created_at))
    )).scalars().all()

    try:
        current_price = await market_data.get_current_price()
    except Exception:
        current_price = 0

    win_rate = 0
    if portfolio and portfolio.total_trades > 0:
        win_rate = round((portfolio.winning_trades / portfolio.total_trades) * 100, 1)

    return {
        "portfolio": {
            "balance": portfolio.balance if portfolio else settings.INITIAL_BALANCE,
            "total_pnl": portfolio.total_pnl if portfolio else 0,
            "total_trades": portfolio.total_trades if portfolio else 0,
            "winning_trades": portfolio.winning_trades if portfolio else 0,
            "losing_trades": portfolio.losing_trades if portfolio else 0,
            "win_rate": win_rate,
            "best_trade": portfolio.best_trade_pnl if portfolio else 0,
            "worst_trade": portfolio.worst_trade_pnl if portfolio else 0,
        },
        "current_price": current_price,
        "pair": settings.DEFAULT_PAIR,
        "open_trades": [_trade_to_dict(t) for t in open_trades],
        "recent_trades": [_trade_to_dict(t) for t in recent_trades],
    }


# ─── Trades ──────────────────────────────────

@router.get("/trades")
async def get_trades(
    status: Optional[str] = None,
    strategy: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """Get trade history with filters."""
    query = select(Trade).order_by(desc(Trade.created_at))

    if status:
        query = query.where(Trade.status == status.upper())
    if strategy:
        query = query.where(Trade.strategy.contains(strategy))

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    trades = result.scalars().all()

    return {"trades": [_trade_to_dict(t) for t in trades], "total": len(trades)}


@router.get("/trades/{trade_id}")
async def get_trade_detail(trade_id: int, session: AsyncSession = Depends(get_session)):
    """Get full trade detail with explanation and post-analysis."""
    trade = (await session.execute(
        select(Trade).where(Trade.id == trade_id)
    )).scalars().first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    explanation = (await session.execute(
        select(TradeExplanation).where(TradeExplanation.trade_id == trade_id)
    )).scalars().first()

    post_analysis = (await session.execute(
        select(PostAnalysis).where(PostAnalysis.trade_id == trade_id)
    )).scalars().first()

    snapshot = (await session.execute(
        select(MarketSnapshot).where(MarketSnapshot.trade_id == trade_id)
    )).scalars().first()

    return {
        "trade": _trade_to_dict(trade),
        "explanation": {
            "full_text": explanation.setup_description,
            "reasons": explanation.reasons,
            "learning_points": explanation.learning_points,
            "risk_reward_ratio": explanation.risk_reward_ratio,
            "indicators": explanation.indicators,
        } if explanation else None,
        "post_analysis": {
            "result_summary": post_analysis.result_summary,
            "what_went_right": post_analysis.what_went_right,
            "what_went_wrong": post_analysis.what_went_wrong,
            "improvements": post_analysis.improvements,
            "lesson": post_analysis.lesson,
        } if post_analysis else None,
        "snapshot": {
            "price": snapshot.price,
            "rsi": snapshot.rsi,
            "macd": snapshot.macd,
            "ema_9": snapshot.ema_9,
            "ema_21": snapshot.ema_21,
            "ema_50": snapshot.ema_50,
            "ema_200": snapshot.ema_200,
            "volume": snapshot.volume,
            "support": snapshot.support_level,
            "resistance": snapshot.resistance_level,
        } if snapshot else None,
    }


# ─── Market Data ─────────────────────────────

@router.get("/market/price")
async def get_price(pair: str = None):
    """Get current price."""
    pair = pair or settings.DEFAULT_PAIR
    price = await market_data.get_current_price(pair)
    return {"pair": pair, "price": price}


@router.get("/market/candles")
async def get_candles(
    pair: str = None,
    timeframe: str = None,
    limit: int = Query(default=100, le=500),
):
    """Get OHLCV candle data for charting with indicator overlays."""
    pair = pair or settings.DEFAULT_PAIR
    timeframe = timeframe or settings.DEFAULT_TIMEFRAME

    df = await market_data.get_candles(pair, timeframe, limit)

    candles = df[["timestamp", "open", "high", "low", "close", "volume"]].to_dict("records")
    for c in candles:
        c["timestamp"] = c["timestamp"].isoformat() if hasattr(c["timestamp"], "isoformat") else str(c["timestamp"])

    # Build overlay data for chart drawing
    def _safe(series):
        """Convert series to list, replacing NaN with None."""
        return [None if (v is None or (isinstance(v, float) and v != v)) else round(v, 2) for v in series]

    timestamps = [c["timestamp"] for c in candles]

    overlays = {
        "ema_9": _safe(df["ema_9"]) if "ema_9" in df.columns else [],
        "ema_21": _safe(df["ema_21"]) if "ema_21" in df.columns else [],
        "ema_50": _safe(df["ema_50"]) if "ema_50" in df.columns else [],
        "ema_200": _safe(df["ema_200"]) if "ema_200" in df.columns else [],
        "bb_upper": _safe(df["bb_upper"]) if "bb_upper" in df.columns else [],
        "bb_middle": _safe(df["bb_middle"]) if "bb_middle" in df.columns else [],
        "bb_lower": _safe(df["bb_lower"]) if "bb_lower" in df.columns else [],
        "timestamps": timestamps,
    }

    # Support/Resistance levels
    support = market_data._find_support(df)
    resistance = market_data._find_resistance(df)

    # Find multiple S/R levels
    sr_levels = market_data.find_sr_levels(df)

    return {
        "pair": pair,
        "timeframe": timeframe,
        "candles": candles,
        "overlays": overlays,
        "support": support,
        "resistance": resistance,
        "sr_levels": sr_levels,
    }


@router.get("/market/indicators")
async def get_indicators(pair: str = None, timeframe: str = None):
    """Get current indicator values."""
    indicators = await market_data.get_indicators(pair, timeframe)
    return indicators


# ─── Strategies ──────────────────────────────

@router.get("/strategies")
async def get_strategies(session: AsyncSession = Depends(get_session)):
    """Get all strategy configurations."""
    result = await session.execute(select(StrategyConfig))
    configs = result.scalars().all()
    return {
        "strategies": [
            {
                "id": c.id,
                "name": c.name,
                "enabled": c.enabled,
                "parameters": c.parameters,
                "description": c.description,
            }
            for c in configs
        ]
    }


@router.put("/strategies/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update strategy config (enable/disable, change parameters)."""
    config = (await session.execute(
        select(StrategyConfig).where(StrategyConfig.id == strategy_id)
    )).scalars().first()

    if not config:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if "enabled" in data:
        config.enabled = data["enabled"]
    if "parameters" in data:
        config.parameters = data["parameters"]

    await session.commit()
    return {"status": "updated", "name": config.name, "enabled": config.enabled}


# ─── Learning / Concepts ─────────────────────

@router.get("/learn/concepts")
async def get_concepts():
    """Get all trading concepts for learning."""
    return {"concepts": get_all_concepts()}


@router.get("/learn/concepts/{concept_name}")
async def get_concept_detail(concept_name: str):
    """Get detailed explanation of a trading concept."""
    concept = get_concept(concept_name)
    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{concept_name}' not found")
    return concept


@router.get("/learn/search")
async def search_concept(q: str):
    """Search trading concepts."""
    results = search_concepts(q)
    return {"query": q, "results": results}


# ─── Performance Analytics ───────────────────

@router.get("/analytics")
async def get_analytics(session: AsyncSession = Depends(get_session)):
    """Get trading performance analytics."""
    all_trades = (await session.execute(
        select(Trade).where(Trade.status == "CLOSED").order_by(Trade.created_at)
    )).scalars().all()

    if not all_trades:
        return {"message": "No closed trades yet", "stats": {}}

    # Strategy performance
    strategy_stats = {}
    for trade in all_trades:
        strat = trade.strategy
        if strat not in strategy_stats:
            strategy_stats[strat] = {"wins": 0, "losses": 0, "total_pnl": 0, "trades": 0}
        strategy_stats[strat]["trades"] += 1
        strategy_stats[strat]["total_pnl"] += trade.pnl or 0
        if trade.pnl and trade.pnl > 0:
            strategy_stats[strat]["wins"] += 1
        else:
            strategy_stats[strat]["losses"] += 1

    for strat in strategy_stats:
        s = strategy_stats[strat]
        s["win_rate"] = round((s["wins"] / s["trades"]) * 100, 1) if s["trades"] > 0 else 0

    # PnL over time
    pnl_history = []
    cumulative = 0
    for trade in all_trades:
        cumulative += trade.pnl or 0
        pnl_history.append({
            "trade_id": trade.id,
            "pnl": trade.pnl,
            "cumulative_pnl": round(cumulative, 2),
            "date": trade.closed_at.isoformat() if trade.closed_at else None,
        })

    return {
        "total_trades": len(all_trades),
        "strategy_performance": strategy_stats,
        "pnl_history": pnl_history,
        "avg_pnl": round(sum(t.pnl or 0 for t in all_trades) / len(all_trades), 2),
        "avg_win": round(
            sum(t.pnl for t in all_trades if t.pnl and t.pnl > 0) /
            max(1, sum(1 for t in all_trades if t.pnl and t.pnl > 0)), 2
        ),
        "avg_loss": round(
            sum(t.pnl for t in all_trades if t.pnl and t.pnl <= 0) /
            max(1, sum(1 for t in all_trades if t.pnl and t.pnl <= 0)), 2
        ),
    }


# ─── Settings ────────────────────────────────

@router.get("/settings")
async def get_settings():
    """Get current bot settings."""
    return {
        "pair": settings.DEFAULT_PAIR,
        "timeframe": settings.DEFAULT_TIMEFRAME,
        "mock_mode": settings.MOCK_MODE,
        "bybit_configured": settings.is_bybit_configured,
        "initial_balance": settings.INITIAL_BALANCE,
    }


# ─── Helpers ─────────────────────────────────

def _trade_to_dict(trade: Trade) -> dict:
    return {
        "id": trade.id,
        "pair": trade.pair,
        "side": trade.side,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "quantity": trade.quantity,
        "stop_loss": trade.stop_loss,
        "take_profit": trade.take_profit,
        "status": trade.status,
        "pnl": trade.pnl,
        "pnl_percent": trade.pnl_percent,
        "strategy": trade.strategy,
        "timeframe": trade.timeframe,
        "confluence_score": trade.confluence_score,
        "created_at": trade.created_at.isoformat() if trade.created_at else None,
        "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
    }
