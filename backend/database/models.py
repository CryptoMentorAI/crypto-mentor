from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pair = Column(String(20), nullable=False)  # e.g. BTC/USDT
    side = Column(String(4), nullable=False)  # BUY or SELL
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    status = Column(String(10), default="OPEN")  # OPEN, CLOSED, CANCELLED
    pnl = Column(Float, nullable=True)  # Profit/Loss in USDT
    pnl_percent = Column(Float, nullable=True)
    strategy = Column(String(50), nullable=False)  # Which strategy triggered
    timeframe = Column(String(5), nullable=False)
    confluence_score = Column(Integer, default=0)  # 1-5
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

    explanation = relationship("TradeExplanation", back_populates="trade", uselist=False)
    post_analysis = relationship("PostAnalysis", back_populates="trade", uselist=False)
    snapshot = relationship("MarketSnapshot", back_populates="trade", uselist=False)


class TradeExplanation(Base):
    __tablename__ = "trade_explanations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    reasons = Column(JSON, nullable=False)  # List of reasons why trade was taken
    indicators = Column(JSON, nullable=False)  # Indicator values at time of trade
    setup_description = Column(Text, nullable=False)  # Full explanation text
    learning_points = Column(JSON, nullable=False)  # What user can learn
    risk_reward_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trade = relationship("Trade", back_populates="explanation")


class PostAnalysis(Base):
    __tablename__ = "post_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    result_summary = Column(Text, nullable=False)  # What happened
    what_went_right = Column(JSON, nullable=True)  # Things that worked
    what_went_wrong = Column(JSON, nullable=True)  # Things that didn't
    improvements = Column(JSON, nullable=True)  # Suggestions
    lesson = Column(Text, nullable=False)  # Key takeaway
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trade = relationship("Trade", back_populates="post_analysis")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    pair = Column(String(20), nullable=False)
    price = Column(Float, nullable=False)
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    ema_9 = Column(Float, nullable=True)
    ema_21 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    ema_200 = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    avg_volume = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    atr = Column(Float, nullable=True)
    adx = Column(Float, nullable=True)
    support_level = Column(Float, nullable=True)
    resistance_level = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trade = relationship("Trade", back_populates="snapshot")


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    balance = Column(Float, nullable=False, default=10000.0)
    total_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    best_trade_pnl = Column(Float, default=0.0)
    worst_trade_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class StrategyConfig(Base):
    __tablename__ = "strategy_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    parameters = Column(JSON, default=dict)  # Strategy-specific params
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
