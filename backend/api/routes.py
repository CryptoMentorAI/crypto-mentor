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


@router.get("/market/analysis")
async def get_market_analysis(pair: str = None, timeframe: str = None):
    """Real-time market analysis with educational insights in Bahasa Melayu."""
    ind = await market_data.get_indicators(pair, timeframe)
    price = ind["price"]
    insights = []

    # ─── RSI Analysis ─────────────────────
    rsi = ind["rsi"]
    if rsi <= 30:
        insights.append({
            "indicator": "RSI",
            "value": rsi,
            "signal": "bullish",
            "overlay": "ema_9",
            "title": f"RSI Oversold ({rsi})",
            "text": f"RSI di bawah 30 — market dah oversold. Ramai seller dah exhausted, kemungkinan besar harga akan bounce naik. Ini macam rubber band yang dah stretch terlalu banyak ke bawah.",
            "tip": "Jangan terus buy — tunggu confirmation macam bullish candle atau RSI mula naik balik atas 30.",
        })
    elif rsi >= 70:
        insights.append({
            "indicator": "RSI",
            "value": rsi,
            "signal": "bearish",
            "overlay": "ema_9",
            "title": f"RSI Overbought ({rsi})",
            "text": f"RSI atas 70 — market dah overbought. Buyer dah terlalu excited, harga mungkin akan pullback turun. Macam kereta yang laju sangat, kena brake.",
            "tip": "Ini bukan signal jual terus — tapi jangan beli sekarang. Tunggu RSI turun bawah 70 dulu.",
        })
    else:
        zone = "neutral"
        desc = "seimbang"
        if rsi > 55:
            zone = "mild_bullish"
            desc = "sedikit bullish"
        elif rsi < 45:
            zone = "mild_bearish"
            desc = "sedikit bearish"
        insights.append({
            "indicator": "RSI",
            "value": rsi,
            "signal": zone,
            "overlay": "ema_9",
            "title": f"RSI {desc.title()} ({rsi})",
            "text": f"RSI kat {rsi} — zone {desc}. Takde extreme signal sekarang. Market bergerak normal.",
            "tip": "RSI paling berguna bila dia masuk zone extreme (bawah 30 atau atas 70).",
        })

    # ─── EMA Trend Analysis ───────────────
    ema9, ema21, ema50 = ind["ema_9"], ind["ema_21"], ind["ema_50"]
    if ema9 > ema21 > ema50:
        insights.append({
            "indicator": "EMA",
            "value": f"{ema9}/{ema21}/{ema50}",
            "signal": "bullish",
            "overlay": "ema_9",
            "title": "EMA Bullish Alignment",
            "text": f"EMA 9 ({ema9:,.0f}) > EMA 21 ({ema21:,.0f}) > EMA 50 ({ema50:,.0f}) — semua moving average beratur naik. Ini tanda uptrend yang kuat.",
            "tip": "Dalam uptrend, harga biasanya bounce dari EMA 21 atau EMA 50. Kalau harga touch EMA 21 dan bounce — itu potential buy zone.",
        })
    elif ema9 < ema21 < ema50:
        insights.append({
            "indicator": "EMA",
            "value": f"{ema9}/{ema21}/{ema50}",
            "signal": "bearish",
            "overlay": "ema_9",
            "title": "EMA Bearish Alignment",
            "text": f"EMA 9 ({ema9:,.0f}) < EMA 21 ({ema21:,.0f}) < EMA 50 ({ema50:,.0f}) — semua MA beratur turun. Market dalam downtrend.",
            "tip": "Dalam downtrend, elakkan buy. Tunggu EMA 9 cross atas EMA 21 (Golden Cross) sebelum consider entry.",
        })
    else:
        insights.append({
            "indicator": "EMA",
            "value": f"{ema9}/{ema21}/{ema50}",
            "signal": "neutral",
            "overlay": "ema_9",
            "title": "EMA Mixed Signal",
            "text": f"EMA tak beratur — market dalam sideways/choppy zone. EMA 9: {ema9:,.0f}, EMA 21: {ema21:,.0f}, EMA 50: {ema50:,.0f}.",
            "tip": "Bila EMA bersilang-silang, market tak ada clear trend. Baik tunggu dia settle dulu sebelum trade.",
        })

    # ─── MACD ─────────────────────────────
    macd_val = ind["macd"]
    macd_sig = ind["macd_signal"]
    macd_hist = ind["macd_histogram"]
    if macd_val > macd_sig and macd_hist > 0:
        insights.append({
            "indicator": "MACD",
            "value": round(macd_hist, 2),
            "signal": "bullish",
            "overlay": "ema_21",
            "title": "MACD Bullish Momentum",
            "text": f"MACD line atas signal line — momentum bullish. Histogram: +{macd_hist:.2f}. Macam enjin kereta yang sedang pick up speed.",
            "tip": "MACD bullish + RSI tak overbought = setup yang bagus untuk buy.",
        })
    elif macd_val < macd_sig and macd_hist < 0:
        insights.append({
            "indicator": "MACD",
            "value": round(macd_hist, 2),
            "signal": "bearish",
            "overlay": "ema_21",
            "title": "MACD Bearish Momentum",
            "text": f"MACD line bawah signal line — momentum bearish. Histogram: {macd_hist:.2f}. Seller masih kuat, harga mungkin terus turun.",
            "tip": "Kalau MACD histogram makin kecil (kurang negatif), itu tanda seller dah mula lemah — potential reversal.",
        })

    # ─── Bollinger Bands ──────────────────
    bb_upper, bb_lower = ind["bb_upper"], ind["bb_lower"]
    bb_width_pct = round(((bb_upper - bb_lower) / price) * 100, 2)
    if price >= bb_upper * 0.998:
        insights.append({
            "indicator": "Bollinger",
            "value": f"Upper: {bb_upper:,.0f}",
            "signal": "bearish",
            "overlay": "bb",
            "title": "Harga di Upper Bollinger Band",
            "text": f"Harga ({price:,.0f}) sentuh upper band ({bb_upper:,.0f}). Biasanya harga akan pullback ke middle band ({ind['bb_middle']:,.0f}).",
            "tip": "Bollinger upper band bukan auto-sell signal, tapi kalau volume rendah — kemungkinan pullback tinggi.",
        })
    elif price <= bb_lower * 1.002:
        insights.append({
            "indicator": "Bollinger",
            "value": f"Lower: {bb_lower:,.0f}",
            "signal": "bullish",
            "overlay": "bb",
            "title": "Harga di Lower Bollinger Band",
            "text": f"Harga ({price:,.0f}) sentuh lower band ({bb_lower:,.0f}). Mean reversion — harga biasa bounce balik ke tengah ({ind['bb_middle']:,.0f}).",
            "tip": "Lower band + RSI oversold = strong bounce signal. Tapi confirm dulu dengan volume.",
        })
    if bb_width_pct < 2:
        insights.append({
            "indicator": "Bollinger",
            "value": f"Width: {bb_width_pct}%",
            "signal": "neutral",
            "overlay": "bb",
            "title": "Bollinger Squeeze!",
            "text": f"Bollinger bands dah ketat ({bb_width_pct}% width). Ini macam spring yang dah compress — breakout besar akan datang!",
            "tip": "Squeeze tak bagitau arah mana. Tunggu candle breakout atas/bawah band, lepas tu follow direction tu.",
        })

    # ─── Volume ───────────────────────────
    vol = ind["volume"]
    avg_vol = ind["avg_volume"]
    if avg_vol > 0:
        vol_ratio = round(vol / avg_vol, 2)
        if vol_ratio >= 2:
            insights.append({
                "indicator": "Volume",
                "value": f"{vol_ratio}x average",
                "signal": "neutral",
                "overlay": "ema_9",
                "title": f"Volume Spike ({vol_ratio}x)",
                "text": f"Volume sekarang {vol_ratio}x dari average — ada big player masuk. Volume tinggi confirm bahawa move sekarang ada 'tenaga' di belakang.",
                "tip": "Breakout dengan volume tinggi = real move. Breakout tanpa volume = fake out, biasa trap.",
            })
        elif vol_ratio < 0.5:
            insights.append({
                "indicator": "Volume",
                "value": f"{vol_ratio}x average",
                "signal": "neutral",
                "overlay": "ema_9",
                "title": "Volume Sangat Rendah",
                "text": f"Volume cuma {vol_ratio}x dari average. Market sunyi — pergerakan harga tak reliable.",
                "tip": "Low volume = jangan trust the move. Tunggu volume masuk baru decide.",
            })

    # ─── ADX Trend Strength ───────────────
    adx = ind["adx"]
    if adx >= 25:
        insights.append({
            "indicator": "ADX",
            "value": adx,
            "signal": "neutral",
            "overlay": "ema_50",
            "title": f"Strong Trend (ADX: {adx})",
            "text": f"ADX {adx} — market ada strong trend sekarang. ADX atas 25 bermaksud trend tu boleh dipercayai.",
            "tip": "Dalam strong trend, trade ikut arah trend (trend following). Jangan cuba lawan trend.",
        })
    elif adx < 20:
        insights.append({
            "indicator": "ADX",
            "value": adx,
            "signal": "neutral",
            "overlay": "ema_50",
            "title": f"Weak/No Trend (ADX: {adx})",
            "text": f"ADX {adx} — takde strong trend. Market sideways. Trend following strategy tak berkesan sekarang.",
            "tip": "Dalam sideways market, guna mean reversion — buy kat support, sell kat resistance.",
        })

    # ─── Overall Sentiment ────────────────
    bullish_count = sum(1 for i in insights if i["signal"] == "bullish")
    bearish_count = sum(1 for i in insights if i["signal"] == "bearish")
    total = len(insights)

    if bullish_count > bearish_count and bullish_count >= 2:
        overall = "bullish"
        summary = f"Majority indicator ({bullish_count}/{total}) tunjuk bullish. Market favor naik."
    elif bearish_count > bullish_count and bearish_count >= 2:
        overall = "bearish"
        summary = f"Majority indicator ({bearish_count}/{total}) tunjuk bearish. Market favor turun."
    else:
        overall = "neutral"
        summary = "Indicator bercampur — takde clear direction. Sabar tunggu confluence."

    return {
        "price": price,
        "pair": pair or settings.DEFAULT_PAIR,
        "timeframe": timeframe or settings.DEFAULT_TIMEFRAME,
        "overall": overall,
        "summary": summary,
        "insights": insights,
        "indicators": ind,
    }


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
