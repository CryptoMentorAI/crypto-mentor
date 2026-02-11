from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .models import Base, Portfolio, StrategyConfig
from backend.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables and seed default data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default portfolio if empty
    async with async_session() as session:
        result = await session.execute(
            Portfolio.__table__.select().limit(1)
        )
        if result.first() is None:
            portfolio = Portfolio(balance=settings.INITIAL_BALANCE)
            session.add(portfolio)

            # Seed default strategy configs
            default_strategies = [
                StrategyConfig(
                    name="technical_analysis",
                    enabled=True,
                    parameters={
                        "rsi_oversold": 30,
                        "rsi_overbought": 70,
                        "rsi_period": 14,
                        "ema_fast": 9,
                        "ema_slow": 21,
                        "macd_fast": 12,
                        "macd_slow": 26,
                        "macd_signal": 9,
                    },
                    description="RSI, MACD, EMA crossover, Bollinger Bands, Volume analysis",
                ),
                StrategyConfig(
                    name="price_action",
                    enabled=True,
                    parameters={
                        "support_lookback": 50,
                        "resistance_lookback": 50,
                        "min_touches": 2,
                        "breakout_threshold": 0.005,
                    },
                    description="Support/Resistance, Candlestick patterns, Breakout detection",
                ),
                StrategyConfig(
                    name="trend_following",
                    enabled=True,
                    parameters={
                        "adx_threshold": 25,
                        "ma_ribbon": [9, 21, 50, 200],
                        "trend_confirmation_candles": 3,
                    },
                    description="MA Ribbon, ADX trend strength, Higher highs/lows",
                ),
                StrategyConfig(
                    name="scalping",
                    enabled=False,  # Disabled by default — advanced
                    parameters={
                        "rsi_period": 7,
                        "vwap_deviation": 0.002,
                        "min_volume_ratio": 1.5,
                        "quick_tp_percent": 0.3,
                    },
                    description="Quick RSI divergence, VWAP deviation, Micro S/R",
                ),
            ]
            session.add_all(default_strategies)
            await session.commit()


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
